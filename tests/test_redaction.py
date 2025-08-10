from fastapi import HTTPException
from api.policy import decide_view_by_scopes

def test_redacted_scope_cannot_request_full():
    scopes = {"objects:read:redacted"}
    try:
        decide_view_by_scopes("full", scopes)
        assert False, "Should have raised 403"
    except HTTPException as e:
        assert e.status_code == 403
        assert e.detail["error"]["code"] == "forbidden"

def test_full_scope_can_request_any():
    scopes = {"objects:read"}
    assert decide_view_by_scopes("full", scopes) == "full"
    assert decide_view_by_scopes("llm_min", scopes) == "llm_min"
    assert decide_view_by_scopes(None, scopes) == "full"

def test_combined_scopes_honor_view_param():
    scopes = {"objects:read", "objects:read:redacted"}
    assert decide_view_by_scopes("full", scopes) == "full"
    assert decide_view_by_scopes("llm_min", scopes) == "llm_min"
    assert decide_view_by_scopes(None, scopes) == "full"

def test_no_read_scope_raises_403():
    scopes = set()
    try:
        decide_view_by_scopes("full", scopes)
        assert False, "Should have raised 403"
    except HTTPException as e:
        assert e.status_code == 403
        assert e.detail["error"]["code"] == "forbidden"
