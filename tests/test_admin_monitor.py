# tests/test_admin_monitor.py

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

# In tests, MM_ENV is set to "test" by tests/conftest.py.
# These headers trigger test-only bypasses in our middlewares.
HEADERS = {
    "X-Bypass-Loop": "true",
    "X-Bypass-RateLimit": "true",
    "X-Bypass-Size": "true",
}

def test_system_status_endpoint_returns_200():
    response = client.get("/admin/system-status", headers=HEADERS)
    # Debug prints to help diagnose if it fails
    print("Status:", response.status_code)
    print("Body:", response.text)
    assert response.status_code == 200

def test_system_status_response_structure():
    response = client.get("/admin/system-status", headers=HEADERS)
    print("Structure Status:", response.status_code, "Body:", response.text)
    data = response.json()

    expected_keys = {
        "uptime_seconds",
        "match_success_count",
        "match_fallback_count",
        "error_count",
    }
    assert expected_keys.issubset(data.keys()), "Missing expected system status keys"

def test_system_status_values_are_numbers():
    response = client.get("/admin/system-status", headers=HEADERS)
    print("Values Status:", response.status_code, "Body:", response.text)
    data = response.json()

    assert isinstance(data["uptime_seconds"], (int, float))
    assert isinstance(data["match_success_count"], int)
    assert isinstance(data["match_fallback_count"], int)
    assert isinstance(data["error_count"], int)
