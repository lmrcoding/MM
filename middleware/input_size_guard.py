# middleware/input_size_guard.py

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from utils.logger import logger
from utils.test_mode import is_test_mode

# A safe default limit for JSON bodies in Phase 1
MAX_INLINE_BYTES = 1024  # 1 KB

class InputSizeGuardMiddleware(BaseHTTPMiddleware):
    """
    Blocks requests with unusually large inline bodies to avoid accidental overloads.
    In test mode, we skip this so pytest can send many quick requests freely.
    """

    async def dispatch(self, request: Request, call_next):
        # Bypass entirely when running tests
        if is_test_mode():
            return await call_next(request)

        # Only check JSON-ish content types
        content_type = request.headers.get("Content-Type", "")
        if "application/json" not in content_type:
            return await call_next(request)

        content_length_header = request.headers.get("Content-Length")
        # If no content-length header, we can't pre-block safely
        if not content_length_header:
            return await call_next(request)

        try:
            clen = int(content_length_header)
        except ValueError:
            # If it's not an integer, just continue (don’t fail the request)
            return await call_next(request)

        if clen > MAX_INLINE_BYTES:
            logger.info("Inline payload check triggered. Content-Length: %d bytes", clen)
            return JSONResponse({"detail": "Payload too large"}, status_code=429)

        # Small enough — continue
        return await call_next(request)
