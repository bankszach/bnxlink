from __future__ import annotations
import json, pathlib, yaml
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from datetime import datetime, timezone
from .security import bearer, Principal
from . import policy

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

app = FastAPI(title="BNX Link Gate", version="0.1.0")


def read_object_by_hash(h: str) -> dict:
    if not h.startswith("sha256:"):
        raise HTTPException(400, "hash must start with sha256:")
    hexf = h.split(":", 1)[1]
    path = DATA / f"objects/{hexf[:2]}/{hexf}.json"
    if not path.exists():
        raise HTTPException(404, f"object not found: {h}")
    return json.loads(path.read_text(encoding="utf-8"))


def audit(line: dict):
    line["ts"] = datetime.now(tz=timezone.utc).isoformat()
    with (DATA / "ledger.ndjson").open("a", encoding="utf-8") as f:
        f.write(json.dumps(line) + "\n")


def project_fields(obj: dict, fields: list[str]) -> dict:
    # simple dot-path projection (read-only)
    out = {}
    for fp in fields:
        cur_in = obj
        parts = fp.split(".")
        for part in parts:
            if isinstance(cur_in, dict) and part in cur_in:
                cur_in = cur_in[part]
            else:
                cur_in = None
                break
        # set into out dict same top-level key
        top = parts[0]
        if cur_in is not None:
            # place under same structure at top-level (flatten to simple keys)
            out[top] = obj.get(top) if len(parts) == 1 else out.get(top, {})
            if len(parts) > 1:
                d = out[top]
                for p in parts[1:-1]:
                    d = d.setdefault(p, {})
                d[parts[-1]] = cur_in
    return out or obj


def apply_view(obj: dict, view: str | None) -> dict:
    if not view or view == "full":
        return obj
    if view == "llm_min":
        # keep envelope (without owner), context, and body minus "links"
        obj2 = {
            "envelope": {k: v for k, v in obj.get("envelope", {}).items() if k not in ("owner",)},
            "context": obj.get("context", {}),
            "body": {k: v for k, v in obj.get("body", {}).items() if k != "links"},
        }
        return obj2
    return obj


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/objects/{hash}")
def get_object(
    hash: str,
    p: Principal = Depends(bearer),
    view: str | None = Query(None, enum=["full", "llm_min"]),
    fields: str | None = None,
):
    obj = read_object_by_hash(hash)
    classification = (
        obj.get("envelope", {}).get("privacy", {}).get("classification", "internal")
    )
    redacted = (view == "llm_min") or (
        "objects:read" not in p.scope and "objects:read:redacted" in p.scope
    )
    policy.allow_read_object(p, classification, redacted, p.purpose)

    body = apply_view(obj, "llm_min" if redacted else view)
    if fields:
        body = project_fields(body, [s.strip() for s in fields.split(",") if s.strip()])

    audit(
        {
            "event": "api.objects.get",
            "sub": p.sub,
            "hash": hash,
            "view": view or ("llm_min" if redacted else "full"),
        }
    )
    return JSONResponse(body)


@app.get("/refs/{ns}/{logical_id}/{date}")
def get_ref(ns: str, logical_id: str, date: str, p: Principal = Depends(bearer)):
    ref_path = DATA / f"refs/{ns}/{logical_id}/{date}.json"
    if not ref_path.exists():
        raise HTTPException(404, "ref not found")
    ref = json.loads(ref_path.read_text(encoding="utf-8"))
    audit({"event": "api.refs.get", "sub": p.sub, "ref": str(ref_path)})
    return ref


@app.get("/manifests/{dataset}/{manifest_id}")
def get_manifest(dataset: str, manifest_id: str, p: Principal = Depends(bearer)):
    # auth
    if "manifests:read" not in p.scope and "objects:read:redacted" not in p.scope:
        raise HTTPException(403, "missing scope")
    path = DATA / f"manifests/{dataset}/{manifest_id}.json"
    if not path.exists():
        raise HTTPException(404, "manifest not found")
    audit(
        {
            "event": "api.manifests.get",
            "sub": p.sub,
            "dataset": dataset,
            "manifest": manifest_id,
        }
    )
    return json.loads(path.read_text(encoding="utf-8"))


@app.post("/manifests")
def post_manifest(payload: dict, p: Principal = Depends(bearer)):
    # simple create; expects {"dataset": "...", "manifest_id": "..."}; collects current refs
    if "manifests:write" not in p.scope:
        raise HTTPException(403, "missing scope manifests:write")
    from scripts.build_manifest import main as build  # reuse code if desired (optional)
    # minimal inline builder to avoid import side-effects:
    import datetime as _dt, copy, hashlib

    dataset = payload["dataset"]
    manifest_id = payload.get("manifest_id") or _dt.datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    items = []
    for ref in (DATA / "refs").rglob("*.json"):
        items.append({"ref": str(ref.relative_to(ROOT)), "hash": json.loads(ref.read_text())["object"]})
    m = {
        "manifest_type": "bnx.manifest.v1",
        "dataset": dataset,
        "manifest_id": manifest_id,
        "created_at": _dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "objects": items,
        "integrity": {"sha256": None},
    }
    tmp = json.dumps({**m, "integrity": {"sha256": None}}, sort_keys=True, separators=(",", ":")).encode()
    m["integrity"]["sha256"] = "sha256:" + hashlib.sha256(tmp).hexdigest()
    path = DATA / f"manifests/{dataset}/{manifest_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(m, indent=2), encoding="utf-8")
    audit(
        {
            "event": "api.manifests.post",
            "sub": p.sub,
            "dataset": dataset,
            "manifest": manifest_id,
        }
    )
    return m


@app.post("/channels/{dataset}/{channel}:promote")
def promote(dataset: str, channel: str, payload: dict, p: Principal = Depends(bearer)):
    if "channels:promote" not in p.scope:
        raise HTTPException(403, "missing scope channels:promote")
    manifest_id: str = payload["manifest"]
    path = DATA / f"manifests/{dataset}/{manifest_id}.json"
    if not path.exists():
        raise HTTPException(404, "manifest not found")
    channels_yml = DATA / "channels.yaml"
    current = (
        yaml.safe_load(channels_yml.read_text(encoding="utf-8")) if channels_yml.exists() else {}
    )
    current.setdefault(dataset, {})
    current[dataset][channel] = manifest_id
    channels_yml.write_text(yaml.safe_dump(current, sort_keys=True), encoding="utf-8")
    audit(
        {
            "event": "api.channels.promote",
            "sub": p.sub,
            "dataset": dataset,
            "channel": channel,
            "manifest": manifest_id,
        }
    )
    return {"ok": True, "dataset": dataset, "channel": channel, "manifest": manifest_id}


