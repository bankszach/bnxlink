from __future__ import annotations
from datetime import datetime

def summarize(objs: list[dict]) -> dict:
    lines = []
    for o in objs:
        kind = o.get("envelope",{}).get("kind","Object")
        b = o.get("body",{})
        if kind == "EntityRecord":
            lines.append(f"Entity '{b.get('entity_id')}' type={b.get('entity_type')} labels={list((b.get('labels') or {}).keys())}")
        elif kind == "ActivityRecord":
            lines.append(f"Activity '{b.get('activity_id')}' status={b.get('status')} due={b.get('scheduling',{}).get('due_date')}")
        else:
            lines.append(f"{kind}")
    return {"type":"bnx.summary","generated_at": datetime.utcnow().isoformat()+'Z', "lines": lines}


