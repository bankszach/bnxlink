from __future__ import annotations
import json, pathlib, yaml
from fastapi import FastAPI, Depends, HTTPException, Query, Request
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from prometheus_fastapi_instrumentator import Instrumentator
from .security import require_bearer, require_scope, settings
from .policy import decide_view_by_scopes
from datetime import datetime

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

app = FastAPI(title="BNX Link API", version="0.1.0")

# Middleware
app.add_middleware(GZipMiddleware, minimum_size=512)
if settings.cors_origins:
    app.add_middleware(CORSMiddleware,
        allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
        allow_methods=["GET","POST","OPTIONS"], allow_headers=["*"])

# Metrics
Instrumentator().instrument(app).expose(app, include_in_schema=False)

def read_object_by_hash(h: str) -> dict:
    if not h.startswith("sha256:"):
        raise HTTPException(status_code=400, detail={"error":{"code":"bad_request","message":"hash must start with sha256:"}})
    hexf = h.split(":", 1)[1]
    path = DATA / f"objects/{hexf[:2]}/{hexf}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail={"error":{"code":"not_found","message":f"object not found: {h}"}})
    return json.loads(path.read_text(encoding="utf-8"))

def load_manifest(dataset: str, manifest_id: str) -> dict:
    path = DATA / f"manifests/{dataset}/{manifest_id}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail={"error":{"code":"not_found","message":f"manifest not found: {dataset}/{manifest_id}"}})
    return json.loads(path.read_text(encoding="utf-8"))

def load_and_apply_view(hash_id: str, view: str) -> dict:
    obj = read_object_by_hash(hash_id)
    if view == "llm_min":
        # keep envelope (without owner), context, and body minus "links"
        obj2 = {
            "envelope": {k: v for k, v in obj.get("envelope", {}).items() if k not in ("owner",)},
            "context": obj.get("context", {}),
            "body": {k: v for k, v in obj.get("body", {}).items() if k != "links"},
        }
        return obj2
    return obj

def do_promote(dataset: str, channel: str, manifest_in, principal):
    """
    Promote a manifest to a channel with normalized storage format.
    
    Args:
        dataset: Dataset name
        channel: Channel name  
        manifest_in: Either manifest ID (string) or full manifest (dict)
        principal: Authenticated principal with user info
    """
    # 1) resolve manifest id + etag
    if isinstance(manifest_in, str):
        manifest_id = manifest_in
        manifest_path = DATA / f"manifests/{dataset}/{manifest_id}.json"
        if not manifest_path.exists():
            raise HTTPException(
                status_code=404, 
                detail={"error": {"code": "not_found", "message": f"manifest not found: {manifest_id}"}}
            )
        manifest = json.loads(manifest_path.read_text())
    elif isinstance(manifest_in, dict):
        manifest = manifest_in
        manifest_id = manifest.get("manifest_id") or manifest.get("id") or "unnamed"
        # optional snapshot if no file exists
        manifest_path = DATA / f"manifests/{dataset}/{manifest_id}.json"
        if not manifest_path.exists():
            manifest_path.parent.mkdir(parents=True, exist_ok=True)
            manifest_path.write_text(json.dumps(manifest, indent=2))
    else:
        raise HTTPException(
            status_code=400, 
            detail={"error": {"code": "bad_request", "message": "manifest must be id or object"}}
        )

    # Extract etag from manifest - handle different manifest structures
    etag = None
    if "envelope" in manifest and "integrity" in manifest["envelope"]:
        etag = manifest["envelope"]["integrity"].get("sha256")
    elif "objects" in manifest and manifest["objects"]:
        # Use first object hash as etag if no envelope integrity
        etag = manifest["objects"][0].get("hash")
    
    if not etag:
        # Fallback: generate a simple etag from manifest_id
        etag = f"sha256:{manifest_id}"

    # 2) load channels, normalize structure
    channels_path = DATA / "channels.yaml"
    if channels_path.exists():
        channels = yaml.safe_load(channels_path.read_text()) or {}
    else:
        channels = {}
    
    ds = channels.setdefault(dataset, {})
    
    # Handle legacy string format channels by converting to dict
    if isinstance(ds.get(channel), str):
        ds[channel] = {}
    
    ch = ds.setdefault(channel, {})

    # move current to history if it changed
    now = datetime.utcnow().isoformat() + "Z"
    by = principal.get("sub") or "unknown"
    new_cur = {"id": manifest_id, "etag": etag, "promoted_at": now, "by": by}

    # Handle legacy string values in current field
    if "current" in ch:
        current = ch["current"]
        if isinstance(current, str):
            # Legacy string format - convert to normalized structure for history
            legacy_current = {"id": current, "etag": f"sha256:{current}", "promoted_at": now, "by": "legacy"}
            ch.setdefault("history", []).append(legacy_current)
        elif isinstance(current, dict) and current.get("id") != manifest_id:
            ch.setdefault("history", []).append(current)

    ch["current"] = new_cur
    
    # Write normalized structure
    channels_path.write_text(yaml.dump(channels, default_flow_style=False))

def etag_json(obj: dict, request: Request) -> Response:
    etag = obj.get("envelope",{}).get("integrity",{}).get("sha256")
    if etag and request.headers.get("if-none-match") == etag:
        return Response(status_code=304)
    headers = {"ETag": etag} if etag else None
    return JSONResponse(obj, headers=headers)

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/objects/{hash_id}")
def get_object(hash_id: str, request: Request, view: str | None = Query(None, enum=["full", "llm_min"]), principal=Depends(require_bearer)):
    view_eff = decide_view_by_scopes(view, principal["scopes"])
    obj = load_and_apply_view(hash_id, view_eff)
    return etag_json(obj, request)

@app.get("/manifests/{dataset}/{manifest_id}")
def get_manifest(dataset: str, manifest_id: str, principal=Depends(require_bearer)):
    require_scope(principal, "manifests:read")
    return JSONResponse(load_manifest(dataset, manifest_id))

@app.post("/channels/{dataset}/{channel}:promote")
def promote_channel(dataset: str, channel: str, body: dict, principal=Depends(require_bearer)):
    require_scope(principal, "channels:promote")
    do_promote(dataset, channel, body["manifest"], principal)
    return {"ok": True}


