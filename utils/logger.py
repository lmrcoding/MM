# utils/logger.py

import logging
import os
from typing import Optional, Any, Dict
from contextvars import ContextVar  # ✅ correct for Python 3.8

# --- Import sanitizer with a safe fallback so imports never fail ---
try:
    from utils.logger_utils import sanitize_log_text
except Exception:
    def sanitize_log_text(message: str) -> str:
        # Fallback: if logger_utils isn't available, don't block imports.
        return message

# ========= Context variables (filled by RequestContextMiddleware) =========
# Tip: On Python 3.8, keep this simple; avoid fancy generics here.
cv_route: ContextVar = ContextVar("route", default=None)
cv_client_ip: ContextVar = ContextVar("client_ip", default=None)
cv_user_agent: ContextVar = ContextVar("user_agent", default=None)
cv_agent_id: ContextVar = ContextVar("agent_id", default=None)
cv_request_id: ContextVar = ContextVar("request_id", default=None)


def set_log_context(route: str, client_ip: str, user_agent: str, agent_id: str, request_id: str) -> None:
    """
    Called by your RequestContextMiddleware to push request-scoped values into context vars.
    """
    cv_route.set(route)
    cv_client_ip.set(client_ip)
    cv_user_agent.set(user_agent)
    cv_agent_id.set(agent_id)
    cv_request_id.set(request_id)


def clear_log_context() -> None:
    """
    Clears context after a request finishes so the next request starts clean.
    """
    cv_route.set(None)
    cv_client_ip.set(None)
    cv_user_agent.set(None)
    cv_agent_id.set(None)
    cv_request_id.set(None)


class ContextEnricherFilter(logging.Filter):
    """
    Injects contextvars into each LogRecord so the formatter can use them.
    If something is missing/empty, we return "-".
    """
    @staticmethod
    def _get(cv: ContextVar, default: str = "-") -> str:
        val = cv.get()
        return val if val else default

    def filter(self, record: logging.LogRecord) -> bool:
        record.route = self._get(cv_route)
        record.client_ip = self._get(cv_client_ip)
        record.user_agent = self._get(cv_user_agent)
        record.agent_id = self._get(cv_agent_id)
        record.request_id = self._get(cv_request_id)
        return True


class ContextDefaultsFilter(logging.Filter):
    """
    Guarantees all expected placeholders exist so the formatter never KeyErrors.
    """
    DEFAULTS: Dict[str, Any] = {
        "request_id": "-",
        "route": "-",
        "client_ip": "-",
        "user_agent": "-",
        "agent_id": "-",
        "method": "-",
        "status_code": "-",
    }

    def filter(self, record: logging.LogRecord) -> bool:
        for key, default in self.DEFAULTS.items():
            if not hasattr(record, key):
                setattr(record, key, default)
        return True


def _build_formatter() -> logging.Formatter:
    fmt = (
        "%(asctime)s | %(levelname)s | req=%(request_id)s route=%(route)s "
        "ip=%(client_ip)s ua=%(user_agent)s agent=%(agent_id)s | %(message)s"
    )
    datefmt = "%Y-%m-%d %H:%M:%S"
    return logging.Formatter(fmt=fmt, datefmt=datefmt)


def _ensure_log_dir() -> str:
    log_dir = os.path.join(os.getcwd(), "logs")
    os.makedirs(log_dir, exist_ok=True)
    return log_dir


# Expose a common path some modules/tests might reference
LOG_FILE_PATH = os.path.join(_ensure_log_dir(), "agent_calls.log")


def _build_file_handler() -> logging.FileHandler:
    handler = logging.FileHandler(LOG_FILE_PATH, encoding="utf-8")
    handler.setLevel(logging.INFO)
    handler.setFormatter(_build_formatter())
    handler.addFilter(ContextEnricherFilter())
    handler.addFilter(ContextDefaultsFilter())
    return handler


def _build_console_handler() -> logging.StreamHandler:
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    handler.setFormatter(_build_formatter())
    handler.addFilter(ContextEnricherFilter())
    handler.addFilter(ContextDefaultsFilter())
    return handler


def _build_base_logger() -> logging.Logger:
    """
    Build a private logger for MM only.
    We do NOT set logging.basicConfig with our placeholders, so third-party
    loggers (e.g., httpx) won't break if they lack our context fields.
    """
    logger = logging.getLogger("MMLogger")
    if logger.handlers:
        return logger  # already configured

    logger.setLevel(logging.INFO)
    logger.addHandler(_build_file_handler())
    logger.addHandler(_build_console_handler())
    logger.propagate = False  # don't bubble to root
    return logger


class SanitizingLogger:
    """
    Wraps the base logger so every message gets sanitized before being written,
    and forces handler flush (helps tests read the most recent line immediately).
    """
    def __init__(self, base_logger: logging.Logger):
        self._logger = base_logger

    def _log(self, method_name: str, message: str, *args, **kwargs):
        sanitized = sanitize_log_text(message)
        getattr(self._logger, method_name)(sanitized, *args, **kwargs)
        for h in self._logger.handlers:
            try:
                h.flush()
            except Exception:
                pass

    def info(self, message: str, *args, **kwargs):
        self._log("info", message, *args, **kwargs)

    def warning(self, message: str, *args, **kwargs):
        self._log("warning", message, *args, **kwargs)

    def error(self, message: str, *args, **kwargs):
        self._log("error", message, *args, **kwargs)

    def debug(self, message: str, *args, **kwargs):
        self._log("debug", message, *args, **kwargs)

    def critical(self, message: str, *args, **kwargs):
        self._log("critical", message, *args, **kwargs)


# Public logger to import everywhere
_base_logger = _build_base_logger()
logger = SanitizingLogger(_base_logger)


__all__ = [
    "logger",
    "set_log_context",
    "clear_log_context",
    "ContextEnricherFilter",
    "ContextDefaultsFilter",
    "LOG_FILE_PATH",
]
