
from fastapi.testclient import TestClient
from apps.orchestrator.app.main import app

client = TestClient(app)

def test_health_orchestrator():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["block"] == "mcp_orchestrator"
