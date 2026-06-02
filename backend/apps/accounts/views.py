"""Accounts views — thin, delegates to services."""
import logging
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from core.responses import success_response, created_response, error_response
from core.throttles import LoginRateThrottle, ForgotPasswordRateThrottle
from . import services
from .models import User, PhoneOTPToken
from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    UserSerializer,
    ChangePasswordSerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer,
    UpdateProfileSerializer,
    PhoneSignupSerializer,
    PhoneLoginSerializer,
    OTPVerifySerializer,
    GoogleAuthSerializer,
)

logger = logging.getLogger("apps.accounts")


# ── Phone OTP flow ─────────────────────────────────────────────────────────────

@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([LoginRateThrottle])
def phone_request_otp(request):
    """POST /auth/phone/request-otp/ — send OTP to phone."""
    serializer = PhoneLoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    phone = serializer.validated_data["phone"]

    PhoneOTPToken.objects.filter(phone=phone, used=False, expires_at__lt=timezone.now()).update(used=True)
    token = PhoneOTPToken.objects.create(
        phone=phone,
        otp=PhoneOTPToken.generate_otp(6),
        expires_at=timezone.now() + timezone.timedelta(minutes=10),
        device_info=request.data.get("device_info", ""),
        ip_address=request.META.get("REMOTE_ADDR"),
    )
    logger.info("OTP generated for phone=%s (masked)", phone[:4] + "****")
    return success_response(
        data={"otp": token.otp, "phone": phone},
        message="OTP sent successfully. (Dev: shown in response.)",
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def phone_verify_otp(request):
    """POST /auth/phone/verify-otp/ — verify OTP, sign up or log in."""
    serializer = OTPVerifySerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    phone = serializer.validated_data["phone"]
    otp = serializer.validated_data["otp"]

    try:
        token = PhoneOTPToken.objects.filter(
            phone=phone, used=False
        ).select_related().latest("created_at")
    except PhoneOTPToken.DoesNotExist:
        return error_response("Invalid or expired OTP.", status_code=400)

    if not token.is_valid() or token.otp != otp:
        return error_response("Invalid or expired OTP.", status_code=400)

    token.used = True
    token.save(update_fields=["used"])

    user = User.objects.filter(phone=phone).first()
    created = False
    if not user:
        user = User.objects.create_user(
            phone=phone,
            first_name="",
            last_name="",
        )
        Profile.objects.create(user=user)
        created = True

    tokens = services.get_tokens_for_user(user)
    return success_response(
        data={
            "tokens": tokens,
            "user": UserSerializer(user, context={"request": request}).data,
            "created": created,
        },
        message="Phone verified successfully." + (" Account created." if created else " Welcome back."),
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def phone_signup(request):
    """POST /auth/phone/signup/ — create account with phone + password."""
    serializer = PhoneSignupSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    if User.objects.filter(phone=data["phone"]).exists():
        return error_response("Phone number already registered.", status_code=400)

    password = data.get("password")
    if not password:
        return error_response("Password is required.", status_code=400)

    user = User.objects.create_user(
        phone=data["phone"],
        first_name=data.get("first_name", ""),
        last_name=data.get("last_name", ""),
        password=password,
    )
    Profile.objects.create(user=user)
    tokens = services.get_tokens_for_user(user)
    return created_response(
        data={"tokens": tokens, "user": UserSerializer(user, context={"request": request}).data},
        message="Account created successfully.",
    )


# ── Google OAuth flow ──────────────────────────────────────────────────────────

@api_view(["POST"])
@permission_classes([AllowAny])
def google_auth(request):
    """POST /auth/google/ — authenticate with Google ID token."""
    serializer = GoogleAuthSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    access_token = serializer.validated_data["access_token"]

    try:
        from google.oauth2 import id_token
        from google.auth.transport import requests as google_requests
    except ImportError:
        import requests as google_requests
        id_token = None

    if id_token:
        try:
            idinfo = id_token.verify_oauth2_token(
                access_token,
                google_requests.Request(),
            )
            email = idinfo.get("email")
            first_name = idinfo.get("given_name", "")
            last_name = idinfo.get("family_name", "")
            picture = idinfo.get("picture", "")
            if not email:
                return error_response("Google account has no email.", status_code=400)
        except Exception as exc:
            logger.warning("Google token verification failed: %s", exc)
            return error_response("Invalid Google token.", status_code=401)
    else:
        try:
            resp = google_requests.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            email = data.get("email")
            first_name = data.get("given_name", "")
            last_name = data.get("family_name", "")
            picture = data.get("picture", "")
        except Exception as exc:
            logger.warning("Google userinfo fetch failed: %s", exc)
            return error_response("Invalid Google token.", status_code=401)

    user = User.objects.filter(email=email).first()
    created = False
    if not user:
        user = User.objects.create_user(
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone="",
        )
        Profile.objects.create(user=user)
        created = True
        user.is_verified = True
        user.save(update_fields=["is_verified"])

    tokens = services.get_tokens_for_user(user)
    return success_response(
        data={
            "tokens": tokens,
            "user": UserSerializer(user, context={"request": request}).data,
            "created": created,
        },
        message="Google sign-in successful." + (" Account created." if created else " Welcome back."),
    )


class RegisterView(generics.CreateAPIView):
    """POST /auth/register/ — Create a new account."""
    permission_classes = [AllowAny]
    throttle_classes = [LoginRateThrottle]
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        services.send_verification_email(user)
        tokens = services.get_tokens_for_user(user)
        return created_response(
            data={
                "tokens": tokens,
                "user": UserSerializer(user, context={"request": request}).data,
            },
            message="Account created. Check your email to verify.",
        )


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([LoginRateThrottle])
def login_view(request):
    """POST /auth/login/ — Authenticate and receive JWT tokens."""
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.validated_data["user"]
    tokens = services.get_tokens_for_user(user)
    return success_response(
        data={
            "tokens": tokens,
            "user": UserSerializer(user, context={"request": request}).data,
        },
        message="Login successful.",
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """POST /auth/logout/ — Blacklist refresh token."""
    try:
        refresh_token = request.data.get("refresh")
        if refresh_token:
            RefreshToken(refresh_token).blacklist()
    except Exception:
        pass
    return success_response(message="Logged out successfully.")


@api_view(["GET"])
@permission_classes([AllowAny])
def verify_email_view(request):
    """GET /auth/verify-email/?token=<uuid> — Verify email address."""
    token = request.query_params.get("token")
    if not token:
        return error_response("Token is required.", status_code=400)
    if services.verify_email(token):
        return success_response(message="Email verified successfully.")
    return error_response("Invalid or expired token.", status_code=400)


class MeView(generics.RetrieveUpdateAPIView):
    """
    GET   /auth/me/ — Current user profile
    PUT   /auth/me/ — Update profile (full replace)
    PATCH /auth/me/ — Partial update
    """
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return UpdateProfileSerializer
        return UserSerializer

    def get_object(self):
        return self.request.user

    def retrieve(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_object())
        return success_response(data=serializer.data)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return success_response(
            data=UserSerializer(user, context={"request": request}).data,
            message="Profile updated successfully.",
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def change_password_view(request):
    """POST /auth/change-password/ — Change password."""
    serializer = ChangePasswordSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    if not request.user.check_password(serializer.validated_data["old_password"]):
        return error_response("Old password is incorrect.", status_code=400)
    request.user.set_password(serializer.validated_data["new_password"])
    request.user.save(update_fields=["password"])
    return success_response(message="Password changed successfully.")


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([ForgotPasswordRateThrottle])
def forgot_password_view(request):
    """POST /auth/forgot-password/ — Send password reset email."""
    serializer = ForgotPasswordSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    services.initiate_password_reset(serializer.validated_data["email"])
    # Always return success to prevent email enumeration
    return success_response(message="If that email is registered, a reset link has been sent.")


@api_view(["POST"])
@permission_classes([AllowAny])
def reset_password_view(request):
    """POST /auth/reset-password/ — Complete password reset."""
    serializer = ResetPasswordSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    services.complete_password_reset(
        serializer.validated_data["reset_token"],
        serializer.validated_data["new_password"],
    )
    return success_response(message="Password reset successfully. You can now log in.")
