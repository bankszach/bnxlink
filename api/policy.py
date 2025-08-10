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


def decide_view_by_scopes(requested_view: str | None, scopes: set[str]) -> str:
    full = "objects:read" in scopes
    red = "objects:read:redacted" in scopes
    if full and red:
        return requested_view or "full"
    if full:
        return requested_view or "full"
    if red:
        if requested_view and requested_view != "llm_min":
            raise HTTPException(status_code=403, detail={"error":{"code":"forbidden","message":"Only redacted view allowed"}})
        return "llm_min"
    raise HTTPException(status_code=403, detail={"error":{"code":"forbidden","message":"No read scope"}})


