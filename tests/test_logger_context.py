# tests/test_logger_context.py

import time
from fastapi.testclient import TestClient
from main import app

LOG_FILE_PATH = "logs/agent_calls.log"
client = TestClient(app)

HEADERS = {
    "X-Bypass-Loop": "true",
    "X-Bypass-RateLimit": "true",
    "X-Bypass-Size": "true",
    "X-Agent-Id": "agent-ctx-test-001",
    "User-Agent": "MM-TestClient/1.0",
}

def read_last_log_line() -> str:
    with open(LOG_FILE_PATH, "r") as f:
        lines = f.readlines()
        return lines[-1] if lines else ""

def test_log_includes_context_fields():
    # Hit the route to trigger RequestContextMiddleware "Request start" log
    res = client.get("/admin/system-status", headers=HEADERS)
    assert res.status_code == 200

    # Allow a brief moment for file flush
    time.sleep(0.2)
    last = read_last_log_line()
    print("Last Log Line:", last)

    # Check core fields
    assert "route=/admin/system-status" in last
    assert "agent=agent-ctx-test-001" in last
    assert "ip=" in last  # should be 127.0.0.1 under TestClient
    assert "req=" in last  # request_id present
