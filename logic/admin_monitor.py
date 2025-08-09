# logic/admin_monitor.py

import time
from typing import Dict
from utils.logger import logger

# Basic system stats
SYSTEM_STATUS = {
    "start_time": time.time(),
    "match_success_count": 0,
    "match_fallback_count": 0,
    "error_count": 0,
}

def increment_stat(key: str):
    if key in SYSTEM_STATUS:
        SYSTEM_STATUS[key] += 1
        logger.info(f"[Monitor] Incremented {key} → {SYSTEM_STATUS[key]}")
    else:
        logger.warning(f"[Monitor] Tried to increment unknown key: {key}")

def get_system_status() -> Dict:
    uptime = time.time() - SYSTEM_STATUS["start_time"]
    status_report = {
        "uptime_seconds": round(uptime, 2),
        "match_success_count": SYSTEM_STATUS["match_success_count"],
        "match_fallback_count": SYSTEM_STATUS["match_fallback_count"],
        "error_count": SYSTEM_STATUS["error_count"],
    }
    return status_report
