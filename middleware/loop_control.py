# middleware/loop_control.py

import time
from collections import defaultdict
from typing import Dict, Tuple
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from utils.test_mode import is_test_mode

# Remember last (method, path, body-hash) per client briefly to avoid loops.
WINDOW_SECONDS = 2.0

class LoopControlMiddleware(BaseHTTPMiddleware):
    """
    Prevents tight client loops by blocking immediately repeated, identical requests.
    In TEST MODE, we skip this so tests can post the same payload multiple times.
    """

    # (client_id, signature) -> last_timestamp
    _seen: Dict[Tuple[str, str], float] = defaultdict(float)

    async def dispatch(self, request: Request, call_next):
        if is_test_mode():
            return await call_next(request)

        client_id = request.client.host if request.client else "unknown"
        path = request.url.path
        method = request.method

        # Build a lightweight signature; avoid reading the whole body
        body_len = request.headers.get("content-length", "0")
        signature = f"{method}:{path}:{body_len}"

        now = time.time()
        key = (client_id, signature)
        last = self._seen.get(key, 0.0)
        if now - last < WINDOW_SECONDS:
            return JSONResponse(
                status_code=429,
                content={"detail": "Repeated identical request detected. Please slow down."},
            )

        self._seen[key] = now
        return await call_next(request)
