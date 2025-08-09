import time
import sys
import os
from fastapi.testclient import TestClient

# Step 1: Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.app import create_app

app = create_app()
client = TestClient(app)


def test_rate_limiter_blocks_second_request():
    # First request (should pass)
    first = client.get("/admin/ping")
    assert first.status_code == 200

    # Wait to avoid triggering loop control
    time.sleep(1.5)

    # Second request (too soon for rate limiter)
    second = client.get("/admin/ping")
    assert second.status_code == 429
    assert second.json()["error"] in [
        "Too many requests — slow down.",
        "Duplicate request detected — possible loop.",
    ]

    # Sleep long enough to reset rate limiter's internal clock
    time.sleep(2)

    # Third request (should now pass cleanly)
    third = client.get("/admin/ping", headers={"X-Bypass-Loop": str(time.time())})
    assert third.status_code == 200
