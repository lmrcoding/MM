# middleware/request_context.py

import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from utils.logger import logger
from utils.logger import (
    set_log_context,
    clear_log_context,
)

class RequestContextMiddleware(BaseHTTPMiddleware):
    """
    Captures request context (route, ip, user-agent, agent_id, request_id)
    and makes it available to the logger via contextvars.
    """

    async def dispatch(self, request: Request, call_next):
        # Gather context
        path = request.url.path
        client_ip = request.client.host if request.client else "0.0.0.0"
        user_agent = request.headers.get("User-Agent", "")
        agent_id = request.headers.get("X-Agent-Id", "")  # optional, if your agents set this
        request_id = str(uuid.uuid4())

        # Attach to log context
        set_log_context(
            route=path,
            client_ip=client_ip,
            user_agent=user_agent,
            agent_id=agent_id,
            request_id=request_id,
        )

        # Log a small entry so tests (and you) can verify context shows up
        logger.info("Request start")

        try:
            response = await call_next(request)
            return response
        finally:
            # Clear context so the next request doesn't reuse these values
            clear_log_context()
