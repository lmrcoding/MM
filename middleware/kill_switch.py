# middleware/kill_switch.py

import os
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from utils.logger import logger
from utils.security import is_test_env

# This constant is imported by the test suite.
# The test writes this file to trigger a 503.
KILL_FILE = "KILL_SWITCH"


class KillSwitchMiddleware(BaseHTTPMiddleware):
    """
    If the KILL_SWITCH file exists, block requests with 503.
    Test-only bypass: send header X-Bypass-Kill: true (used manually, not by tests).
    """

    async def dispatch(self, request: Request, call_next):
        # Optional test-only bypass: only honored if you're explicitly sending the header
        # AND you're in test mode. The test cases do not set this header.
        if is_test_env() and request.headers.get("X-Bypass-Kill") == "true":
            return await call_next(request)

        if os.path.exists(KILL_FILE):
            logger.warning("Kill switch active. All agent logic is paused.")
            return JSONResponse(
                status_code=503,
                content={"detail": "Kill switch active. All agent logic is paused."},
            )

        return await call_next(request)
