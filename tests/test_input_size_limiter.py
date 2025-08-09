import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi.testclient import TestClient
from core.app import create_app

app = create_app()
client = TestClient(app)

def test_inline_payload_logger():
    payload = {"name": "Logger Test", "query": "Log my payload size"}
    response = client.post("/agent/run", json=payload)
    assert response.status_code in [200, 429, 413]
