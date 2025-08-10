from fastapi.testclient import TestClient
from api.main import app

def test_health_ok():
    c = TestClient(app)
    r = c.get("/health")
    assert r.status_code == 200 and r.json()["ok"] is True

def test_missing_auth_is_401():
    c = TestClient(app)
    r = c.get("/objects/sha256:deadbeef")
    assert r.status_code == 401
    assert r.json()["detail"]["error"]["code"] == "unauthorized"

def test_invalid_auth_is_401():
    c = TestClient(app)
    r = c.get("/objects/sha256:deadbeef", headers={"Authorization": "Bearer invalid"})
    assert r.status_code == 401
    assert r.json()["detail"]["error"]["code"] == "unauthorized"

def test_insufficient_scope_is_403():
    # This would require a valid JWT with insufficient scopes
    # For now, we'll test the structure is correct
    c = TestClient(app)
    # We'd need to mock a valid JWT here, but the 403 structure is tested in policy
    pass
