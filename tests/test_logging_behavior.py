# ✅ Full Updated Code for MM Phase 1 - Logging Behavior Test

import os
import time
from core.app import create_app
from starlette.testclient import TestClient

LOG_FILE_PATH = "logs/agent_calls.log"
app = create_app()
client = TestClient(app)

def test_logging_creates_file_and_entry():
    # Truncate the log file if it exists (instead of deleting)
    if os.path.exists(LOG_FILE_PATH):
        with open(LOG_FILE_PATH, "w", encoding="utf-8") as f:
            f.truncate(0)

    # Make a test request to trigger a log entry
    payload = {"name": "Logger Test", "query": "Refill my inventory"}
    response = client.post("/agent/run", json=payload)

    assert response.status_code in (200, 206)

    # Give time for async log flush
    time.sleep(0.5)

    # Check if log file was created
    assert os.path.exists(LOG_FILE_PATH)

    # Check if expected content exists in the log
    with open(LOG_FILE_PATH, "r", encoding="utf-8") as f:
        contents = f.read()
        assert "Logger Test" in contents or "inventory" in contents
