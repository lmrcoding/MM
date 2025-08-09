from starlette.testclient import TestClient
from core.app import create_app

app = create_app()
client = TestClient(app)


def test_fallback_triggered_when_no_match_found():
    payload = {
        "name": "Fallback Tester",
        "query": "How do I pet a unicorn?"  # nonsense to guarantee no match
    }

    response = client.post("/agent/run", json=payload)

    assert response.status_code == 200

    data = response.json()
    content = str(data).lower()

    assert "fallback" in content or "no match" in content or "try again" in content
