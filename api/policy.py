from __future__ import annotations
from fastapi import HTTPException


# super simple RBAC+purpose; swap to OPA next sprint
def require_scope(p, needed: str):
    if needed not in p.scope:
        raise HTTPException(status_code=403, detail=f"missing scope {needed}")


def allow_read_object(p, classification: str, redacted: bool, purpose: str | None):
    # deny restricted unless we had special scope (not added yet)
    if classification == "restricted":
        raise HTTPException(status_code=403, detail="restricted")
    if redacted:
        require_scope(p, "objects:read:redacted")
    else:
        require_scope(p, "objects:read")
    # simple purpose binding: if purpose is set, only allow "analysis" or "planning"
    if p.purpose and p.purpose not in ("analysis", "planning"):
        raise HTTPException(status_code=403, detail=f"purpose {p.purpose} denied")


