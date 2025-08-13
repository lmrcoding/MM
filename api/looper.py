# api/looper.py

from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, Response
import hmac
import hashlib
import time

from utils.logger import logger
from utils.security import is_test_env, is_ip_allowlisted, get_env

# ------------------------------
# Config
# ------------------------------
FRESHNESS_WINDOW_SECONDS = 300  # 5 minutes
MM_INTERNAL_SECRET = get_env("MM_INTERNAL_SECRET", "")


def verify_internal_bypass_signature(sig: str, ts: str, path: str, secret: str) -> bool:
    """
    Verify HMAC-SHA256(sig) over message f"{ts}:{path}" using the shared secret.
    Uses constant-time compare to avoid timing side channels.
    """
    if not (sig and ts and path and secret):
        return False

    try:
        # Enforce timestamp freshness to prevent replay attacks
        ts_val = float(ts)
        if abs(time.time() - ts_val) > FRESHNESS_WINDOW_SECONDS:
            return False
    except (TypeError, ValueError):
        return False

    msg = f"{ts}:{path}".encode("utf-8")
    key = secret.encode("utf-8")
    expected = hmac.new(key, msg, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, sig)


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
        # Conditions:
        #  - Caller marks as internal: X-Internal-Agent: true
        #  - Caller is on allowlisted IP
        #  - Caller presents valid HMAC (X-Internal-Bypass, X-Bypass-Ts)
        # ------------------------------
        if request.headers.get("X-Internal-Agent") == "true":
            if is_ip_allowlisted(client_ip):
                provided_sig = request.headers.get("X-Internal-Bypass") or ""
                ts = request.headers.get("X-Bypass-Ts") or ""
                if MM_INTERNAL_SECRET and verify_internal_bypass_signature(
                    provided_sig, ts, path, MM_INTERNAL_SECRET
                ):
                    return await call_next(request)
                else:
                    logger.warning(
                        "[LoopControl] Invalid or expired bypass signature",
                        extra={"route": path, "client_ip": client_ip}
                    )
            else:
                logger.warning(
                    "[LoopControl] Bypass rejected (IP not allowlisted)",
                    extra={"route": path, "client_ip": client_ip}
                )

        # ------------------------------
        # NORMAL LOOP DETECTION (simple in-memory example)
        # ------------------------------
        loop_key = f"{path}:{request.headers.get('User-Agent','')}"
        recent = getattr(request.state, "recent_calls", set())
        if loop_key in recent:
            logger.warning(
                "[LoopControl] Loop detected",
                extra={"route": path, "client_ip": client_ip}
            )
            return Response(
                content='{"error": "Duplicate request detected — possible loop."}',
                status_code=429,
                media_type="application/json"
            )

        request.state.recent_calls = recent | {loop_key}
        return await call_next(request)
