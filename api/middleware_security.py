from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from middleware.rate_limiter import RateLimiterMiddleware
from middleware.input_size_guard import InputSizeGuardMiddleware
from middleware.loop_control import LoopControlMiddleware
from middleware.kill_switch import KillSwitchMiddleware
from middleware.request_context import RequestContextMiddleware
from utils.logger import logger
from utils.security import is_test_env  # for test-only bypass on inline limiter

# Limit request payloads to 2MB
MAX_INPUT_SIZE_MB = 2

def attach_middleware(app: FastAPI) -> None:
    """
    Attach middlewares in a safe, logical order so request context exists
    before other components log anything.
    """
    # 1) Emergency stop
    app.add_middleware(KillSwitchMiddleware)

    # 2) Request context (so all later logs have route/ip/ua/agent_id)
    app.add_middleware(RequestContextMiddleware)

    # 3) Rate limiting (cheap)
    app.add_middleware(RateLimiterMiddleware)

    # 4) Loop protection
    app.add_middleware(LoopControlMiddleware)

    # 5) Class-based size guard
    app.add_middleware(InputSizeGuardMiddleware)

    # 6) Inline header-based size limiter (fast path)
    @app.middleware("http")
    async def inline_input_size_limiter(request: Request, call_next):
        """
        Very fast cutoff using Content-Length header.

        Test-only bypass (MM_ENV=test):
          Any of these headers will bypass *during tests only*:
            - X-Bypass-Loop: true
            - X-Bypass-RateLimit: true
            - X-Bypass-Size: true
        """
        if is_test_env() and (
            request.headers.get("X-Bypass-Loop") == "true"
            or request.headers.get("X-Bypass-RateLimit") == "true"
            or request.headers.get("X-Bypass-Size") == "true"
        ):
            return await call_next(request)

        content_length = request.headers.get("content-length")
        if content_length:
            try:
                cl_val = int(content_length)
            except ValueError:
                cl_val = None

            logger.info(f"Inline payload check triggered. Content-Length: {content_length} bytes")

            if cl_val is not None and cl_val > MAX_INPUT_SIZE_MB * 1024 * 1024:
                logger.warning("Payload rejected by inline size limiter.")
                return JSONResponse(
                    status_code=413,
                    content={"detail": f"Payload too large. Limit is {MAX_INPUT_SIZE_MB}MB."},
                )

        return await call_next(request)
