import sys
import os
import time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi.testclient import TestClient
from core.app import create_app

app = create_app()
client = TestClient(app)

KILL_FILE = "kill_switch.txt"

def test_kill_switch_blocks_requests():
    # 🛑 Create the kill switch file
    with open(KILL_FILE, "w") as f:
        f.write("emergency maintenance")

    # 🧪 Attempt a request — should be blocked
    response = client.post("/agent/run", json={"name": "Test", "query": "anything"})
    assert response.status_code == 503
    assert "Kill switch" in response.json()["detail"]

    # 🧹 Cleanup
    os.remove(KILL_FILE)
