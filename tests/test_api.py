"""End-to-end tests of the HTTP endpoints, using FastAPI's test client."""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_dashboard_endpoint():
    r = client.get("/api/dashboard")
    assert r.status_code == 200
    data = r.json()
    assert len(data["viruses"]) == 3
    assert data["is_sample"] is True


def test_index_page_served():
    r = client.get("/")
    assert r.status_code == 200
    assert "What's Going Around" in r.text
