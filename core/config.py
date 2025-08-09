import os
from pydantic import BaseSettings

class Settings(BaseSettings):
    ENV: str = "development"
    DEBUG: bool = True
    API_VERSION: str = "v1"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "default_dev_secret")
    RATE_LIMIT: int = 100  # requests per minute per user
    MAX_PAYLOAD_SIZE_MB: int = 2

    class Config:
        env_file = ".env"

settings = Settings()
