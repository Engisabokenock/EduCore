"""
Security utilities: input sanitization, rate limiting helpers, validator mixins.
"""
import ipaddress
import logging
import re
from typing import Optional

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)

KENYA_PHONE_RE = re.compile(r"^(\+?254|0)?[17]\d{8}$")
EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")
UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$", re.IGNORECASE)

ALLOWED_FILE_EXTENSIONS = {"pdf", "doc", "docx", "png", "jpg", "jpeg", "webp", "mp4", "zip"}
MAX_FILE_SIZE_MB = 20


def validate_kenya_phone(phone: str) -> str:
    digits = re.sub(r"\D", "", phone)
    if not KENYA_PHONE_RE.match(digits):
        raise ValueError("Invalid Kenyan phone number. Expected format: 07XXXXXXXX or 254XXXXXXXXX")
    if digits.startswith("07") and len(digits) == 10:
        return "254" + digits[1:]
    if digits.startswith("254") and len(digits) == 12:
        return digits
    if len(digits) == 9:
        return "254" + digits
    raise ValueError("Phone number must be 9 digits after country code.")


def validate_email(email: str) -> str:
    email = email.strip().lower()
    if not EMAIL_RE.match(email):
        raise ValueError("Invalid email address.")
    if len(email) > 254:
        raise ValueError("Email address is too long.")
    return email


def validate_uuid(value: str) -> str:
    if not UUID_RE.match(value):
        raise ValueError("Invalid UUID format.")
    return value.strip().lower()


def sanitize_filename(filename: str) -> str:
    name = re.sub(r"[^\w\s\-\.\(\)\_]", "", filename)
    name = re.sub(r"\s+", " ", name).strip()
    if not name:
        name = "unnamed"
    return name[:200]


def validate_file_extension(filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_FILE_EXTENSIONS:
        raise ValueError(f"File type .{ext} is not allowed. Allowed: {', '.join(sorted(ALLOWED_FILE_EXTENSIONS))}")
    return ext


def validate_file_size(size_bytes: int) -> None:
    max_bytes = MAX_FILE_SIZE_MB * 1024 * 1024
    if size_bytes > max_bytes:
        raise ValueError(f"File size exceeds {MAX_FILE_SIZE_MB}MB limit.")


def is_private_ip(ip: str) -> bool:
    try:
        addr = ipaddress.ip_address(ip)
        return addr.is_private
    except ValueError:
        return False


def get_client_ip(request) -> str:
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        ip = forwarded.split(",")[0].strip()
    else:
        ip = request.META.get("REMOTE_ADDR", "0.0.0.0")
    return ip if not is_private_ip(ip) else "0.0.0.0"


class RateLimitMiddleware(MiddlewareMixin):
    """
    Per-IP rate limiting for sensitive endpoints:
    - /auth/login/        -> 5 per minute
    - /auth/register/     -> 3 per minute
    - /commerce/callback/ -> 10 per hour (redundancy, also in DRF throttle)
    """

    RULES = {
        "/auth/login/":    {"limit": 5,  "window": 60,   "key": "rl:login"},
        "/auth/register/": {"limit": 3,  "window": 60,   "key": "rl:register"},
        "/commerce/subscriptions/pay/": {"limit": 2, "window": 3600, "key": "rl:pay"},
        "/admin/":         {"limit": 30, "window": 60,   "key": "rl:admin"},
    }

    def process_request(self, request):
        if request.method != "POST":
            return None
        for prefix, rule in self.RULES.items():
            if request.path_info.endswith(prefix) or prefix in request.path_info:
                ip = get_client_ip(request)
                key = cache_key(rule["key"], ip)
                count = cache.get(key, 0)
                if count >= rule["limit"]:
                    from django.http import JsonResponse
                    logger.warning("Rate limit exceeded: %s from %s", request.path_info, ip)
                    return JsonResponse(
                        {
                            "success": False,
                            "status_code": 429,
                            "message": "Too many requests. Please try again later.",
                            "data": None,
                            "errors": {"rate_limit": f"{rule['limit']} requests per {rule['window']}s"},
                        },
                        status=429,
                    )
                try:
                    cache.set(key, count + 1, rule["window"])
                except Exception:
                    logger.warning("Rate-limit cache set failed for %s", key)
        return None


def cache_key(*parts: str, prefix: str = "educore") -> str:
    return f"{prefix}:" + ":".join(str(p) for p in parts if p)
