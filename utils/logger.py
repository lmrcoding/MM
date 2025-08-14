# utils/logger.py - FINAL WORKING ENHANCED VERSION (stdlib-compatible)
# Fixed phone pattern to not interfere with credit cards
# Updated to support standard logging call signatures: logger.info("...", *args)

import logging
import logging.handlers
import os
import re
import gzip
import time
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
import shutil

# -----------------------------
# Basic masking helpers
# -----------------------------
def mask_email(text: str) -> str:
    """Replace the user part of emails with *** (john@x.com -> ***@x.com)."""
    email_pattern = r'([a-zA-Z0-9_.+-]+)@([a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)'
    return re.sub(email_pattern, r'***@\2', text)

def mask_phone(text: str) -> str:
    """
    Masks phone numbers (10+ digits) without catching credit-card-like groups.
    """
    phone_pattern = r'(\+?\d{1,2}[\s\-\.]?)?\(?\d{3}\)?[\s\-\.]?\d{3}[\s\-\.]?\d{4}(?!\d)'
    return re.sub(phone_pattern, '***REDACTED PHONE***', text)

def sanitize_log_text(text: str) -> str:
    text = mask_email(text)
    text = mask_phone(text)
    return text

def sanitize_for_logging(text: str) -> str:
    """
    Enhanced sanitization:
      1) emails
      2) credit cards (16 digits with optional separators)
      3) phones
      4) secrets/keys/tokens
      5) bearer tokens
    """
    if not isinstance(text, str):
        text = str(text)

    # 1) Email
    text = mask_email(text)

    # 2) Credit cards
    text = re.sub(
        r'\b\d{4}[\s\-]*\d{4}[\s\-]*\d{4}[\s\-]*\d{4}\b',
        '***REDACTED CARD***',
        text
    )

    # 3) Phone
    phone_pattern = r'(?<!\d)\(?(\+?\d{1,2}[\s\-\.]?)?\d{3}\)?[\s\-\.]?\d{3}[\s\-\.]?\d{4}(?!\d)'
    text = re.sub(phone_pattern, '***REDACTED PHONE***', text)

    # 4) Secrets
    text = re.sub(
        r'(token|apikey|api_key|password|secret|key)\s*[=:]\s*\S+',
        r'\1=***REDACTED***',
        text,
        flags=re.IGNORECASE
    )

    # 5) Bearer tokens
    text = re.sub(
        r'Bearer\s+[A-Za-z0-9\-_\.]+',
        'Bearer ***REDACTED***',
        text
    )

    return text

# -----------------------------
# Redacting formatter (final pass)
# -----------------------------
_SECRET_REGEX = re.compile(r"(?i)\b(apikey|api_key|secret|password|token)\s*[:=]\s*[^,\s]+")

class RedactingFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        msg = super().format(record)
        # final safeguard
        return _SECRET_REGEX.sub(lambda m: f"{m.group(1)}=[REDACTED]", msg)

# -----------------------------
# Rotating + compressing handler
# -----------------------------
class CompressedRotatingFileHandler(logging.handlers.RotatingFileHandler):
    """
    Rotates at 50MB (default) and gzips old files. Keeps backupCount files.
    """
    def __init__(
        self,
        filename,
        mode='a',
        maxBytes=50*1024*1024,
        backupCount=30,
        encoding=None,
        delay=False,
        compress_after_rotate=True
    ):
        super().__init__(filename, mode, maxBytes, backupCount, encoding, delay)
        self.compress_after_rotate = compress_after_rotate

    def doRollover(self):
        if self.stream:
            self.stream.close()
            self.stream = None

        if self.backupCount > 0:
            for i in range(self.backupCount - 1, 0, -1):
                sfn = self.rotation_filename(f"{self.baseFilename}.{i}")
                dfn = self.rotation_filename(f"{self.baseFilename}.{i+1}")
                if os.path.exists(sfn):
                    if os.path.exists(dfn):
                        os.remove(dfn)
                    os.rename(sfn, dfn)

            dfn = self.rotation_filename(self.baseFilename + ".1")
            if os.path.exists(dfn):
                os.remove(dfn)
            self.rotate(self.baseFilename, dfn)

            if self.compress_after_rotate:
                self._compress_file(dfn)

        if not self.delay:
            self.stream = self._open()

    def _compress_file(self, filepath: str):
        try:
            gz_path = filepath + ".gz"
            with open(filepath, "rb") as f_in, gzip.open(gz_path, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
            os.remove(filepath)
        except Exception:
            # keep uncompressed on failure
            pass

# -----------------------------
# Performance tracker
# -----------------------------
class PerformanceTracker:
    def __init__(self):
        self.start_times: Dict[str, float] = {}
        self.performance_threshold = 1000  # ms

    def start_tracking(self, request_id: str):
        self.start_times[request_id] = time.time()

    def end_tracking(self, request_id: str) -> Dict[str, Any]:
        if request_id not in self.start_times:
            return {}
        end = time.time()
        start = self.start_times.pop(request_id)
        dur_ms = (end - start) * 1000.0
        return {
            "duration_ms": round(dur_ms, 2),
            "is_slow": dur_ms > self.performance_threshold,
            "start_time": start,
            "end_time": end,
        }

# -----------------------------
# Context filters (safe defaults)
# -----------------------------
class ContextEnricherFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return True

class ContextDefaultsFilter(logging.Filter):
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
        for k, v in self.DEFAULTS.items():
            if not hasattr(record, k):
                setattr(record, k, v)
        return True

# -----------------------------
# Enhanced/JSON formatter support
# -----------------------------
class EnhancedFormatter(logging.Formatter):
    def __init__(self, use_json: bool = False):
        self.use_json = use_json
        if not use_json:
            fmt = (
                "%(asctime)s | %(levelname)s | req=%(request_id)s route=%(route)s "
                "ip=%(client_ip)s ua=%(user_agent)s agent=%(agent_id)s | %(message)s"
            )
            datefmt = "%Y-%m-%d %H:%M:%S"
            super().__init__(fmt=fmt, datefmt=datefmt)
        else:
            super().__init__()

    def format(self, record: logging.LogRecord) -> str:
        if not self.use_json:
            # Standard text + redaction by RedactingFormatter later
            return super().format(record)
        # JSON structure
        out = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", "-"),
            "route": getattr(record, "route", "-"),
            "client_ip": getattr(record, "client_ip", "-"),
            "user_agent": getattr(record, "user_agent", "-"),
            "agent_id": getattr(record, "agent_id", "-"),
            "method": getattr(record, "method", "-"),
            "status_code": getattr(record, "status_code", "-"),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        if record.exc_info:
            out["exception"] = self.formatException(record.exc_info)
        if hasattr(record, "performance"):
            out["performance"] = record.performance
        return json.dumps(out, default=str)

def _build_formatter(use_json: bool = False) -> logging.Formatter:
    # Chain EnhancedFormatter -> RedactingFormatter for a final redaction pass
    base = EnhancedFormatter(use_json=use_json)
    # Wrap enhanced formatter with a redacting layer
    class _Wrapper(RedactingFormatter):
        def __init__(self, inner: logging.Formatter):
            super().__init__(fmt=inner._fmt if hasattr(inner, "_fmt") else None,
                             datefmt=getattr(inner, "datefmt", None))
            self._inner = inner
        def format(self, record: logging.LogRecord) -> str:
            # use inner first (may be JSON or text), then redact
            raw = self._inner.format(record)
            return _SECRET_REGEX.sub(lambda m: f"{m.group(1)}=[REDACTED]", raw)
    return _Wrapper(base)

def _ensure_log_dir() -> str:
    log_dir = os.path.join(os.getcwd(), "logs")
    os.makedirs(log_dir, exist_ok=True)
    return log_dir

LOG_FILE_PATH = os.path.join(_ensure_log_dir(), "agent_calls.log")

def _build_file_handler(use_rotation: bool = True, use_json: bool = False) -> logging.Handler:
    if use_rotation:
        handler = CompressedRotatingFileHandler(
            LOG_FILE_PATH,
            encoding="utf-8",
            maxBytes=50 * 1024 * 1024,
            backupCount=30,
            compress_after_rotate=True,
        )
    else:
        handler = logging.FileHandler(LOG_FILE_PATH, encoding="utf-8")

    handler.setLevel(logging.INFO)
    handler.setFormatter(_build_formatter(use_json=use_json))
    handler.addFilter(ContextEnricherFilter())
    handler.addFilter(ContextDefaultsFilter())
    return handler

def _build_console_handler() -> logging.StreamHandler:
    h = logging.StreamHandler()
    h.setLevel(logging.INFO)
    h.setFormatter(_build_formatter(use_json=False))
    h.addFilter(ContextEnricherFilter())
    h.addFilter(ContextDefaultsFilter())
    return h

def _build_base_logger(use_rotation: bool = True, use_json_logs: bool = False) -> logging.Logger:
    logger = logging.getLogger("MMLogger")
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    try:
        logger.addHandler(_build_file_handler(use_rotation=use_rotation, use_json=use_json_logs))
    except Exception:
        # Non-fatal if file logging fails
        pass
    logger.addHandler(_build_console_handler())
    logger.propagate = False
    return logger

# -----------------------------
# SanitizingLogger (now stdlib-compatible)
# -----------------------------
class SanitizingLogger:
    """
    Wrapper that:
      - Accepts (msg, *args, **kwargs) like logging.Logger
      - Formats with % if args are provided
      - Sanitizes the final string
      - Logs via base logger
    """
    def __init__(self, base_logger: logging.Logger):
        self.base_logger = base_logger
        self.performance_tracker = PerformanceTracker()

    @staticmethod
    def _format_then_sanitize(msg: Any, args: Tuple[Any, ...]) -> str:
        if args:
            try:
                # Perform %-style formatting like stdlib would
                msg = str(msg) % args
                args = ()
            except Exception:
                # If formatting fails, fall back to simple str(msg)
                msg = str(msg)
        else:
            msg = str(msg)
        return sanitize_for_logging(msg)

    # ---- standard methods ----
    def info(self, msg: Any, *args, **kwargs):
        safe = self._format_then_sanitize(msg, args)
        self.base_logger.info(safe, **kwargs)

    def warning(self, msg: Any, *args, **kwargs):
        safe = self._format_then_sanitize(msg, args)
        self.base_logger.warning(safe, **kwargs)

    def error(self, msg: Any, *args, **kwargs):
        safe = self._format_then_sanitize(msg, args)
        self.base_logger.error(safe, **kwargs)

    def debug(self, msg: Any, *args, **kwargs):
        safe = self._format_then_sanitize(msg, args)
        self.base_logger.debug(safe, **kwargs)

    # ---- perf helpers ----
    def start_performance_tracking(self, request_id: str):
        self.performance_tracker.start_tracking(request_id)

    def end_performance_tracking(self, request_id: str, operation_name: str = "request"):
        metrics = self.performance_tracker.end_tracking(request_id)
        if metrics:
            level = self.warning if metrics["is_slow"] else self.info
            level("Performance: %s took %sms", operation_name, metrics["duration_ms"])
        return metrics

# -----------------------------
# Public API
# -----------------------------
def setup_logger(use_rotation: bool = True, use_json_logs: bool = False) -> SanitizingLogger:
    base_logger = _build_base_logger(use_rotation=use_rotation, use_json_logs=use_json_logs)
    return SanitizingLogger(base_logger)

def flush_all_handlers():
    logger = logging.getLogger("MMLogger")
    for handler in logger.handlers:
        try:
            handler.flush()
        except Exception as e:
            print(f"Warning: Failed to flush log handler: {e}")

def log_with_context(level: str, message: str, *args, **context):
    """
    Accepts *args (for %-style formatting) and optional context.
    Context is sanitized but not injected into the record to avoid ContextVar issues.
    """
    base = logging.getLogger("MMLogger")
    try:
        formatted = (message % args) if args else message
    except Exception:
        formatted = message
    safe_message = sanitize_for_logging(formatted)
    getattr(base, level.lower(), base.info)(safe_message)

# Create the enhanced logger instance (rotation enabled by default)
logger = setup_logger(use_rotation=True, use_json_logs=False)

# Convenience helpers
def log_request_start(request_id: str, route: str, client_ip: str, user_agent: str, agent_id: str = "-"):
    logger.start_performance_tracking(request_id)
    logger.info("Request start: %s from %s", route, client_ip)

def log_request_end(request_id: str, status_code: int, route: str = "-"):
    logger.end_performance_tracking(request_id, f"request {route}")
    logger.info("Request end: %s - Status: %s", route, status_code)

def log_security_event(event_type: str, details: str, **context):
    logger.warning("Security Event: %s - %s", event_type, details)

def log_error_with_context(error: Exception, message: str, **context):
    logger.error("%s - %s: %s", message, type(error).__name__, str(error))

def get_log_stats() -> Dict[str, Any]:
    log_dir = Path(_ensure_log_dir())
    stats: Dict[str, Any] = {
        "log_directory": str(log_dir),
        "total_files": 0,
        "total_size_bytes": 0,
        "compressed_files": 0,
        "files": [],
    }
    for f in log_dir.iterdir():
        if f.is_file():
            st = f.stat()
            stats["total_files"] += 1
            stats["total_size_bytes"] += st.st_size
            stats["files"].append({
                "name": f.name,
                "size_bytes": st.st_size,
                "modified": datetime.fromtimestamp(st.st_mtime).isoformat(),
                "compressed": f.suffix == ".gz",
            })
            if f.suffix == ".gz":
                stats["compressed_files"] += 1
    return stats

__all__ = [
    "logger",
    "log_with_context",
    "log_request_start",
    "log_request_end",
    "log_security_event",
    "log_error_with_context",
    "flush_all_handlers",
    "get_log_stats",
    "mask_email",
    "mask_phone",
    "sanitize_log_text",
    "sanitize_for_logging",
]
