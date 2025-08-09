import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi.testclient import TestClient
from core.app import create_app

app = create_app()
client = TestClient(app)

def test_admin_ping_works():
    response = client.get("/admin/ping")
    assert response.status_code == 200
    assert response.json() == {
        "status": "OK",
        "message": "Metro Match API is running"
    }
