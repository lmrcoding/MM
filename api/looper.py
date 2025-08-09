# api/looper.py

from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, Response
from utils.logger import logger
from utils.security import (
    is_test_env, is_ip_allowlisted, verify_internal_bypass_signature, get_env
)

class LoopControlMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        client_ip = request.client.host if request.client else "0.0.0.0"

        # ------------------------------
        # TEST MODE BYPASS (pytest/unit tests only)
        # Works only when MM_ENV=test (set in tests/conftest.py)
        # ------------------------------
        if is_test_env() and request.headers.get("X-Bypass-Loop") == "true":
            return await call_next(request)

        # ------------------------------
        # (Optional) PRODUCTION/STAGING: secure internal bypass
        # Allow only if:
        #  - Caller marks as internal: X-Internal-Agent: true
        #  - Caller is on allowlisted IP
        #  - Caller presents valid HMAC (X-Internal-Bypass, X-Bypass-Ts)
        # ------------------------------
        if request.headers.get("X-Internal-Agent") == "true":
            if is_ip_allowlisted(client_ip):
                provided_sig = request.headers.get("X-Internal-Bypass") or ""
                ts = request.headers.get("X-Bypass-Ts") or ""
                secret = get_env("MM_INTERNAL_SECRET", "")
                if secret and verify_internal_bypass_signature(provided_sig, ts, path, secret):
                    return await call_next(request)
                else:
                    logger.warning(
                        f"[LoopControl] Invalid bypass signature from {client_ip} for {path}"
                    )
            else:
                logger.warning(
                    f"[LoopControl] Bypass rejected (IP not allowlisted): {client_ip} for {path}"
                )

        # ------------------------------
        # NORMAL LOOP DETECTION (simple in-memory example)
        # ------------------------------
        loop_key = f"{path}:{request.headers.get('User-Agent','')}"
        recent = getattr(request.state, "recent_calls", set())
        if loop_key in recent:
            logger.warning(f"[LoopControl] Loop detected on {path} from {client_ip}")
            return Response(
                content='{"error": "Duplicate request detected — possible loop."}',
                status_code=429,
                media_type="application/json"
            )

        request.state.recent_calls = recent | {loop_key}
        return await call_next(request)
