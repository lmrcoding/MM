# api/routes/admin_monitor.py

from fastapi import APIRouter
from logic.admin_monitor import get_system_status

router = APIRouter(
    prefix="/admin",
    tags=["Admin Monitoring"]
)

@router.get("/system-status")
def system_status():
    """
    Returns current system statistics for the admin dashboard.
    """
    return get_system_status()
