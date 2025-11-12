
from fastapi.testclient import TestClient
from apps.listening_channel.app.main import app

client = TestClient(app)

def test_health_listening():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["block"] == "listening_channel"
