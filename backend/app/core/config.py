import logging
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import PostgresDsn, RedisDsn, Field

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True
    )

    # Core Application Settings
    APP_NAME: str = "EduCore"
    APP_ENV: Literal["development", "staging", "production"] = "development"
    SECRET_KEY: str = Field(..., description="Cryptographic signing key for access tokens")
    JWT_SECRET_KEY: str = Field(..., description="Alias matching system specs")
    JWT_REFRESH_SECRET: str = Field(..., description="Cryptographic signing key for refresh tokens")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Infrastructure Backends
    DATABASE_URL: str
    REDIS_URL: str

    # Cloudflare R2 / AWS S3 Integration
    CLOUDFLARE_ENDPOINT: str
    CLOUDFLARE_ACCESS_KEY: str
    CLOUDFLARE_SECRET_KEY: str
    BUCKET_NAME: str = "educore-assets"

    # M-Pesa Daraja API Integration Parameters
    MPESA_ENVIRONMENT: Literal["sandbox", "production"] = "sandbox"
    MPESA_CONSUMER_KEY: str = Field(..., description="Safaricom Developer Portal Consumer Key")
    MPESA_CONSUMER_SECRET: str = Field(..., description="Safaricom Developer Portal Consumer Secret")
    MPESA_SHORTCODE: str = Field(..., description="M-Pesa Paybill or Buy Goods Till Number")
    MPESA_PASSKEY: str = Field(..., description="Lipa Na M-Pesa Online Passkey for password derivation")
    MPESA_CALLBACK_URL: str = Field(..., description="Public HTTPS endpoint accessible by Safaricom edge servers")

    # Logging Parameters
    LOG_LEVEL: str = "INFO"

settings = Settings()

# Configure Application Logging Globally
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("educore")
