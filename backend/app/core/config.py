import logging
from typing import List, Literal, Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_INSECURE_SECRET_DEFAULTS = {
    "",
    "change-me-in-production",
    "change-me-in-production-jwt",
    "change-me-in-production-refresh",
}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="ignore"
    )

    # ── Core application ─────────────────────────────────────────────────────
    APP_NAME: str = "EduCore"
    APP_ENV: Literal["development", "staging", "production"] = "development"
    FRONTEND_URL: str = "http://localhost:3000"
    # The single account allowed to hold the Super Admin role.
    PLATFORM_OWNER_EMAIL: str = "isabokenock@gmail.com"
    # Comma-separated list of browser origins allowed to call the API directly.
    # The Next.js app proxies /api/* server-side, so in most deployments only the
    # frontend origin itself needs to be listed here.
    CORS_ORIGINS: str = ""

    # NOTE: override these in every real environment via environment variables.
    SECRET_KEY: str = "change-me-in-production"
    JWT_SECRET_KEY: str = "change-me-in-production-jwt"
    JWT_REFRESH_SECRET: str = "change-me-in-production-refresh"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    PASSWORD_RESET_TOKEN_TTL_MINUTES: int = 60

    # ── Infrastructure ───────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/educore"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 10
    REDIS_URL: Optional[str] = "redis://localhost:6379/0"

    # When the API sits behind a reverse proxy / load balancer (nginx, Railway,
    # Render, Cloudflare), the TCP peer is the proxy. Enable this so the real client
    # IP is read from X-Forwarded-For for rate limiting and audit logs.
    TRUST_PROXY_HEADERS: bool = True

    # ── Rate limiting (per client IP, sliding 60s window) ────────────────────
    RATE_LIMIT_PER_MINUTE: int = 240
    AUTH_RATE_LIMIT_PER_MINUTE: int = 10

    # ── Business rules ───────────────────────────────────────────────────────
    DAILY_FREE_DOWNLOAD_LIMIT: int = 5
    SUBSCRIPTION_GRACE_PERIOD_DAYS: int = 3

    # ── Object storage (Cloudflare R2 / S3) ──────────────────────────────────
    CLOUDFLARE_ENDPOINT: Optional[str] = None
    CLOUDFLARE_ACCESS_KEY: Optional[str] = None
    CLOUDFLARE_SECRET_KEY: Optional[str] = None
    BUCKET_NAME: str = "educore-assets"
    # Optional public/CDN base URL for the bucket (e.g. https://cdn.educore.co.ke).
    # When unset, downloads are served through short-lived presigned URLs.
    PUBLIC_ASSET_BASE_URL: Optional[str] = None
    PRESIGNED_URL_TTL_SECONDS: int = 600
    MAX_UPLOAD_SIZE_MB: int = 25

    # ── M-Pesa Daraja ────────────────────────────────────────────────────────
    MPESA_ENVIRONMENT: Literal["sandbox", "production"] = "sandbox"
    MPESA_CONSUMER_KEY: Optional[str] = None
    MPESA_CONSUMER_SECRET: Optional[str] = None
    MPESA_SHORTCODE: Optional[str] = None
    # Till numbers (Buy Goods) collect into a different PartyB than the shortcode.
    MPESA_TILL_NUMBER: Optional[str] = None
    MPESA_TRANSACTION_TYPE: Literal["CustomerPayBillOnline", "CustomerBuyGoodsOnline"] = "CustomerPayBillOnline"
    MPESA_PASSKEY: Optional[str] = None
    # Public HTTPS base URL of the callback endpoint, e.g.
    # https://api.educore.co.ke/api/v1/payments/mpesa/callback
    MPESA_CALLBACK_URL: Optional[str] = None
    # Shared secret appended to the callback URL (?token=...). Daraja callbacks are
    # unauthenticated, so this is what stops forged "payment succeeded" requests.
    MPESA_CALLBACK_SECRET: Optional[str] = None

    # ── Logging ──────────────────────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"

    @field_validator("REDIS_URL", mode="before")
    @classmethod
    def _blank_redis_is_none(cls, value):
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def cors_origins(self) -> List[str]:
        origins = [o.strip().rstrip("/") for o in self.CORS_ORIGINS.split(",") if o.strip()]
        if self.FRONTEND_URL:
            origins.append(self.FRONTEND_URL.strip().rstrip("/"))
        if not self.is_production:
            origins += ["http://localhost:3000", "http://127.0.0.1:3000"]
        # Preserve order, drop duplicates
        return list(dict.fromkeys(origins))

    @property
    def mpesa_configured(self) -> bool:
        return all([
            self.MPESA_CONSUMER_KEY, self.MPESA_CONSUMER_SECRET,
            self.MPESA_SHORTCODE, self.MPESA_PASSKEY, self.MPESA_CALLBACK_URL,
        ])

    @property
    def storage_configured(self) -> bool:
        return all([self.CLOUDFLARE_ENDPOINT, self.CLOUDFLARE_ACCESS_KEY, self.CLOUDFLARE_SECRET_KEY])


settings = Settings()

# Configure application logging globally
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("educore")

_insecure = [
    name for name in ("SECRET_KEY", "JWT_SECRET_KEY", "JWT_REFRESH_SECRET")
    if getattr(settings, name) in _INSECURE_SECRET_DEFAULTS
]
if _insecure:
    if settings.is_production:
        # Refuse to boot: with a known signing key anyone can mint admin tokens.
        raise RuntimeError(
            f"Refusing to start in production with insecure default secrets: {', '.join(_insecure)}"
        )
    logger.critical(
        "SECURITY WARNING: %s use insecure defaults. Set strong unique values via environment variables.",
        ", ".join(_insecure),
    )
if settings.JWT_SECRET_KEY == settings.JWT_REFRESH_SECRET:
    logger.warning("JWT_SECRET_KEY and JWT_REFRESH_SECRET should be different values.")
