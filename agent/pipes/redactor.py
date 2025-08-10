from __future__ import annotations

def apply_llm_min(obj: dict) -> dict:
    env = {k:v for k,v in obj.get("envelope",{}).items() if k not in ("owner",)}
    body = {k:v for k,v in obj.get("body",{}).items() if k != "links"}
    return {"envelope": env, "context": obj.get("context",{}), "body": body}


