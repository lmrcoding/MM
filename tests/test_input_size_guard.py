# ✅ Final clean version
from starlette.testclient import TestClient
from core.app import create_app

app = create_app()
client = TestClient(app)

def test_payload_under_limit():
    small_payload = {"name": "Test User", "query": "Short query"}
    response = client.post("/agent/run", json=small_payload)
    assert response.status_code == 200

def test_payload_over_limit():
    big_text = "x" * (2 * 1024 * 1024 + 1)  # Slightly over 2MB
    large_payload = {"name": "Test User", "query": big_text}
    response = client.post("/agent/run", json=large_payload)
    assert response.status_code == 413
    assert response.json()["detail"] == "Payload too large. Limit is 2MB."
