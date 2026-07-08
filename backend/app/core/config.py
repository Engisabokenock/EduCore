import logging
from typing import Literal, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import PostgresDsn, RedisDsn, Field

logger = logging.getLogger("educore")

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True
    )

    # Core Application Settings
    APP_NAME: str = "EduCore"
    APP_ENV: Literal["development", "staging", "production"] = "development"
    FRONTEND_URL: Optional[str] = None
    # NOTE: override these in every real environment via environment variables.
    SECRET_KEY: str = "change-me-in-production"
    JWT_SECRET_KEY: str = "change-me-in-production-jwt"
    JWT_REFRESH_SECRET: str = "change-me-in-production-refresh"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Infrastructure Backends
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/educore"
    REDIS_URL: str = "redis://localhost:6379/0"

    # Cloudflare R2 / AWS S3 Integration (optional — only required for file storage)
    CLOUDFLARE_ENDPOINT: Optional[str] = None
    CLOUDFLARE_ACCESS_KEY: Optional[str] = None
    CLOUDFLARE_SECRET_KEY: Optional[str] = None
    BUCKET_NAME: str = "educore-assets"

    # M-Pesa Daraja API Integration Parameters (optional — only required for payments)
    MPESA_ENVIRONMENT: Literal["sandbox", "production"] = "sandbox"
    MPESA_CONSUMER_KEY: Optional[str] = None
    MPESA_CONSUMER_SECRET: Optional[str] = None
    MPESA_SHORTCODE: Optional[str] = None
    MPESA_PASSKEY: Optional[str] = None
    MPESA_CALLBACK_URL: Optional[str] = None

    # Logging Parameters
    LOG_LEVEL: str = "INFO"

settings = Settings()

# Fail-loud guard: warn prominently if the insecure default secrets are still in use,
# especially in production. Override SECRET_KEY/JWT_* via environment variables.
if settings.SECRET_KEY in ("change-me-in-production", ""):
    logger.critical(
        "SECURITY WARNING: SECRET_KEY is using the insecure default. "
        "Set a strong unique SECRET_KEY (and JWT_SECRET_KEY/JWT_REFRESH_SECRET) via environment variables."
    )

# Configure Application Logging Globally
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("educore")
