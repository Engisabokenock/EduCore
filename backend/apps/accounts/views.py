"""Accounts views — thin, delegates to services."""
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from core.responses import success_response, created_response, error_response
from core.throttles import LoginRateThrottle, ForgotPasswordRateThrottle
from . import services
from .models import User
from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    UserSerializer,
    ChangePasswordSerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer,
    UpdateProfileSerializer,
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
