from __future__ import annotations
import json, hashlib, pathlib, datetime, typing as t

def canonical_json(obj: t.Any) -> bytes:
    # Deterministic JSON: UTF-8, sorted keys, no extra spaces
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")

def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def write_text(path: str, content: str) -> None:
    p = pathlib.Path(path); p.parent.mkdir(parents=True, exist_ok=True); p.write_text(content, encoding="utf-8")

def read_json(path: str) -> dict:
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))

def now_iso() -> str:
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
