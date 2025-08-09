# utils/security.py

import hmac
import os
import time
from hashlib import sha256
from typing import Optional

def get_env(name: str, default: Optional[str] = None) -> Optional[str]:
    """Read an environment variable, or use a default if missing."""
    val = os.getenv(name)
    return val if val is not None else default

def constant_time_compare(a: str, b: str) -> bool:
    """Timing-safe compare to avoid tiny timing leaks."""
    return hmac.compare_digest(a.encode("utf-8"), b.encode("utf-8"))

def is_test_env() -> bool:
    """Return True if app runs in test mode (MM_ENV=test)."""
    return get_env("MM_ENV", "prod").lower() == "test"

def is_ip_allowlisted(ip: str) -> bool:
    """
    Return True if the IP looks like an internal/private address.
    Adjust to your VPC/CIDR list if needed.
    """
    private_prefixes = ("10.", "192.168.", "172.16.")
    return ip.startswith("127.") or any(ip.startswith(p) for p in private_prefixes)

def verify_internal_bypass_signature(
    provided_sig: str,
    timestamp: str,
    path: str,
    secret: str,
) -> bool:
    """
    Verify a signed internal bypass:
      X-Internal-Bypass: <hex hmac>
      X-Bypass-Ts: <unix seconds>
    Message is f"{timestamp}:{path}" signed with secret.
    """
    try:
        ts = int(timestamp)
    except (TypeError, ValueError):
        return False

    skew = int(get_env("MM_BYPASS_SKEW_SECONDS", "120"))  # default 2 minutes
    now = int(time.time())
    if abs(now - ts) > skew:
        return False

    msg = f"{ts}:{path}".encode("utf-8")
    expected = hmac.new(secret.encode("utf-8"), msg, sha256).hexdigest()
    return constant_time_compare(provided_sig, expected)
