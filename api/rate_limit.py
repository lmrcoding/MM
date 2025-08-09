from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import time

RATE_LIMIT = 60  # max 60 requests per minute per user
user_timestamps = {}

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        ip = request.client.host
        current_time = time.time()

        request_times = user_timestamps.get(ip, [])
        request_times = [t for t in request_times if current_time - t < 60]

        if len(request_times) >= RATE_LIMIT:
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please wait before retrying."}
            )

        request_times.append(current_time)
        user_timestamps[ip] = request_times

        return await call_next(request)

def attach_rate_limiter(app):
    app.add_middleware(RateLimitMiddleware)
