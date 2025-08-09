import sys
import os
import time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi.testclient import TestClient
from core.app import create_app

app = create_app()
client = TestClient(app)

def test_loop_control_blocks_repeated_identical_request():
    payload = {"name": "Loop User", "query": "Refill inventory"}

    # First request (allowed)
    first = client.post("/agent/run", json=payload)
    assert first.status_code == 200

    # ✅ Wait 1.1 seconds to avoid rate limit
    time.sleep(1.1)

    # Second request (same payload) — should be blocked by loop control now
    second = client.post("/agent/run", json=payload)
    assert second.status_code == 429
    assert second.json()["error"] == "Duplicate request detected — possible loop."
