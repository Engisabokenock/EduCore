"""Rate-limit throttle classes for EduCore API endpoints."""
from rest_framework.throttling import AnonRateThrottle


class LoginRateThrottle(AnonRateThrottle):
    """10 login attempts per hour per IP — brute-force protection."""
    scope = "login"


class ForgotPasswordRateThrottle(AnonRateThrottle):
    """5 password-reset requests per hour per IP."""
    scope = "forgot_password"
