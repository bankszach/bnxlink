from fastapi.testclient import TestClient
from fastapi import Depends
from api.main import app
from api import main as m

def test_etag_roundtrip(monkeypatch):
    def fake_loader(h, v): 
        return {"envelope":{"integrity":{"sha256":"X"}}, "body":{}}
    monkeypatch.setattr(m, "load_and_apply_view", fake_loader)
    
    # Create a test app with mocked dependencies
    from fastapi import FastAPI
    test_app = FastAPI()
    
    @test_app.get("/objects/{hash_id}")
    def get_object(hash_id: str, request: m.Request):
        view_eff = m.decide_view_by_scopes(None, {"objects:read"})
        obj = fake_loader(hash_id, view_eff)
        return m.etag_json(obj, request)
    
    c = TestClient(test_app)
    r1 = c.get("/objects/sha256:any")
    assert r1.status_code == 200
    et = r1.headers["etag"]
    r2 = c.get("/objects/sha256:any", headers={"If-None-Match": et})
    assert r2.status_code == 304

def test_etag_missing_returns_200(monkeypatch):
    def fake_loader(h, v): 
        return {"body": {}}  # No envelope.integrity.sha256
    monkeypatch.setattr(m, "load_and_apply_view", fake_loader)
    
    # Create a test app with mocked dependencies
    from fastapi import FastAPI
    test_app = FastAPI()
    
    @test_app.get("/objects/{hash_id}")
    def get_object(hash_id: str, request: m.Request):
        view_eff = m.decide_view_by_scopes(None, {"objects:read"})
        obj = fake_loader(hash_id, view_eff)
        return m.etag_json(obj, request)
    
    c = TestClient(test_app)
    r = c.get("/objects/sha256:any")
    assert r.status_code == 200
    assert "etag" not in r.headers
