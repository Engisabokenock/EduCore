"""Request network helpers shared by rate limiting, audit logs and telemetry."""
from starlette.requests import HTTPConnection

from app.core.config import settings


def get_client_ip(request: HTTPConnection) -> str:
    """
    Resolve the originating client IP.

    Behind a reverse proxy the TCP peer is the proxy itself, which would make every
    visitor share one rate-limit bucket. When TRUST_PROXY_HEADERS is enabled the left-most
    address of X-Forwarded-For (or Cloudflare's CF-Connecting-IP) is used instead.
    """
    if settings.TRUST_PROXY_HEADERS:
        cf_ip = request.headers.get("cf-connecting-ip")
        if cf_ip:
            return cf_ip.strip()[:45]
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            first = forwarded.split(",")[0].strip()
            if first:
                return first[:45]
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip.strip()[:45]
    return (request.client.host if request.client else "0.0.0.0")[:45]


def get_country_code(request: HTTPConnection, default: str = "KE") -> str:
    """Cloudflare geolocation header (ISO alpha-2), falling back to Kenya."""
    code = (request.headers.get("cf-ipcountry") or default).strip().upper()
    return code[:3] if code.isalpha() else default


def get_user_agent(request: HTTPConnection, limit: int = 255) -> str:
    return (request.headers.get("user-agent") or "unknown")[:limit]
