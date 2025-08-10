from fastapi.testclient import TestClient
from api.main import app

def test_metrics_ok():
    c = TestClient(app)
    r = c.get("/metrics")
    assert r.status_code == 200
    assert "http_requests_total" in r.text or "http_server_requests" in r.text

def test_metrics_content_type():
    c = TestClient(app)
    r = c.get("/metrics")
    assert r.headers["content-type"] == "text/plain; version=0.0.4; charset=utf-8"
