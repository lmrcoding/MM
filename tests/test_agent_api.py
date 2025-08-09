import time
from fastapi.testclient import TestClient
from core.app import create_app

app = create_app()
client = TestClient(app)

def test_agent_run_valid():
    payload = {"name": "Test User", "query": "I need help with inventory"}
    response = client.post("/agent/run", json=payload, headers={"X-Test-Case": "1"})
    assert response.status_code == 200
    time.sleep(1.1)

def test_agent_run_empty_field():
    payload = {"name": "Test User", "query": ""}
    response = client.post("/agent/run", json=payload, headers={"X-Test-Case": "2"})
    assert response.status_code == 200
    time.sleep(1.1)

def test_agent_run_missing_query_key():
    payload = {"name": "Test User"}  # missing 'query'
    response = client.post("/agent/run", json=payload, headers={"X-Test-Case": "3"})
    assert response.status_code == 422
    time.sleep(1.1)

def test_agent_run_invalid_json_format():
    response = client.post(
        "/agent/run",
        data="this is not JSON",
        headers={
            "Content-Type": "application/json",
            "X-Test-Case": "4"
        }
    )
    assert response.status_code == 422
