"""Django middleware — maintenance, IP whitelist, security headers, signed-URL helpers."""
import logging
import time
import hashlib
import hmac
import base64
import re
from urllib.parse import urlencode

from django.conf import settings
from django.core.cache import cache
from django.urls import resolve, Resolver404
from django.utils.deprecation import MiddlewareMixin
from django.utils.encoding import force_bytes

logger = logging.getLogger("config.middleware")


# ── Helpers for signed URLs ──────────────────────────────────────────────────────

def _build_signed_url(path: str, ttl_seconds: int = 30) -> str:
    """Build a time-limited signed URL for *path* (e.g. /media/resources/...)."""
    expires = int(time.time()) + ttl_seconds
    sign_string = f"{path}:{expires}"
    secret = settings.MEDIA_SIGNING_SECRET.encode()
    signature = hmac.new(secret, sign_string.encode(), hashlib.sha256).hexdigest()[:16]
    params = urlencode({"expires": expires, "sig": signature})
    separator = "&" if "?" in path else "?"
    return f"{path}{separator}{params}"


def _validate_signed_url(path: str, expires: str, sig: str) -> bool:
    """Return True if the URL signature is valid and not expired."""
    try:
        expires_int = int(expires)
    except (TypeError, ValueError):
        return False
    if expires_int < int(time.time()):
        return False
    sign_string = f"{path}:{expires_int}"
    secret = settings.MEDIA_SIGNING_SECRET.encode()
    expected = hmac.new(secret, sign_string.encode(), hashlib.sha256).hexdigest()[:16]
    return hmac.compare_digest(expected, sig)


# ── Maintenance mode ────────────────────────────────────────────────────────────

MAINTENANCE_PATH_RE = re.compile(
    r"^/(api/v1/health/|admin/|readiness/|liveness/)", re.IGNORECASE
)


class MaintenanceMiddleware:
    """Reject non-exempt requests when MAINTENANCE_MODE is enabled."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if getattr(settings, "MAINTENANCE_MODE", False):
            if not MAINTENANCE_PATH_RE.match(request.path_info):
                from django.http import JsonResponse
                return JsonResponse(
                    {
                        "success": False,
                        "status_code": 503,
                        "message": "Service is under maintenance. Please try again later.",
                        "data": None,
                        "errors": {"maintenance": True},
                    },
                    status=503,
                )
        return self.get_response(request)


# ── IP whitelist middleware ─────────────────────────────────────────────────────

class IPWhitelistMiddleware:
    """Allow only whitelisted IPs for admin if IP_WHITELIST is configured."""

    def __init__(self, get_response):
        self.get_response = get_response
        self.whitelist = [ip.strip() for ip in getattr(settings, "IP_WHITELIST", []) if ip.strip()]

    def __call__(self, request):
        if not self.whitelist:
            return self.get_response(request)
        if request.path_info.startswith("/admin/") or request.path_info.startswith("/api/v1/admin/"):
            remote = request.META.get("REMOTE_ADDR", "")
            forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
            client_ip = forwarded.split(",")[0].strip() if forwarded else remote
            if client_ip not in self.whitelist:
                from django.http import JsonResponse
                return JsonResponse(
                    {"success": False, "status_code": 403, "message": "Access denied from this IP.", "data": None, "errors": None},
                    status=403,
                )
        return self.get_response(request)


# ── Security headers middleware ─────────────────────────────────────────────────

class SecurityHeadersMiddleware:
    """Enforce strict security headers on every response."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response["X-Content-Type-Options"] = "nosniff"
        response["X-Frame-Options"] = "DENY"
        response["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        if not settings.DEBUG:
            response["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
            response["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' data:; "
                "connect-src 'self'; "
                "frame-ancestors 'none';"
            )
        return response


# ── Request logging middleware ──────────────────────────────────────────────────

class RequestLoggingMiddleware(MiddlewareMixin):
    """Log every incoming request at DEBUG level."""

    def process_request(self, request):
        request._start_time = time.time()
        return None

    def process_response(self, request, response):
        if hasattr(request, "_start_time"):
            duration = (time.time() - request._start_time) * 1000
            logger.debug(
                "%s %s %s %s %.1fms",
                request.method,
                request.path_info,
                response.status_code,
                request.META.get("REMOTE_ADDR", "?"),
                duration,
            )
        return response


class DynamicHostMiddleware(MiddlewareMixin):
    """Auto-allow Railway/Render/Fly dynamic host headers so /health/ and API stay reachable."""

    _DYNAMIC_SUFFIXES = (".railway.app", ".up.railway.app", ".onrender.com", ".fly.dev")

    def process_request(self, request):
        host = request.get_host().split(":")[0]
        if not host:
            return None
        if any(host.endswith(s) for s in self._DYNAMIC_SUFFIXES):
            if host not in settings.ALLOWED_HOSTS:
                settings.ALLOWED_HOSTS.append(host)
        return None
