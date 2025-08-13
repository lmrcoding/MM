# core/config.py
import os
from pydantic import BaseSettings, ValidationError, Field

class Settings(BaseSettings):
    """
    Centralized application settings loaded from environment variables.
    NOTE: No default for SECRET_KEY — this will fail fast if missing.
    """

    # App / runtime
    ENV: str = Field(default="development", description="Environment name")
    DEBUG: bool = Field(default=True, description="Enable debug mode")
    API_VERSION: str = Field(default="v1", description="Public API version")

    # Security (REQUIRED)
    # 🚫 No default! If SECRET_KEY isn't provided, app startup will fail with a clear error.
    SECRET_KEY: str = Field(..., description="Application secret key for signing/encryption")

    # Controls
    RATE_LIMIT: int = Field(default=100, description="Requests per minute per user")
    MAX_PAYLOAD_SIZE_MB: int = Field(default=2, description="Max request payload size (MB)")

    class Config:
        # Pydantic v1 settings
        env_file = ".env"
        case_sensitive = True

# Instantiate settings at import time (fail fast if required env is missing)
try:
    settings = Settings()
except ValidationError as e:
    # Raise a clear, safe message (does NOT print secret values)
    missing = []
    for err in e.errors():
        loc = ".".join(str(x) for x in err.get("loc", []))
        if err.get("type", "").startswith("value_error.missing"):
            missing.append(loc)
    missing_msg = f"Missing required environment variable(s): {', '.join(missing)}" if missing else "Invalid settings configuration."
    raise RuntimeError(missing_msg)
