"""Accounts business logic — keep views thin."""
import logging
from datetime import timedelta

from django.db import transaction as db_transaction
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User, EmailVerificationToken, PasswordResetToken

logger = logging.getLogger("apps.accounts")


def get_tokens_for_user(user: User) -> dict:
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }


def create_email_verification_token(user: User) -> EmailVerificationToken:
    with db_transaction.atomic():
        # select_for_update prevents two concurrent registrations from both
        # seeing zero existing tokens and both creating one
        EmailVerificationToken.objects.select_for_update().filter(
            user=user, used=False
        ).update(used=True)
        return EmailVerificationToken.objects.create(
            user=user,
            expires_at=timezone.now() + timedelta(hours=24),
        )


def verify_email(token_uuid: str) -> bool:
    with db_transaction.atomic():
        try:
            token = (
                EmailVerificationToken.objects
                .select_for_update()
                .select_related("user")
                .get(token=token_uuid)
            )
        except EmailVerificationToken.DoesNotExist:
            return False
        if not token.is_valid():
            return False
        token.used = True
        token.save(update_fields=["used"])
        token.user.is_verified = True
        token.user.save(update_fields=["is_verified"])
        return True


def send_verification_email(user: User) -> None:
    token = create_email_verification_token(user)
    verify_url = f"{settings.FRONTEND_URL}/verify-email?token={token.token}"
    try:
        send_mail(
            subject="Verify your EduCore account",
            message=f"Click the link to verify your email: {verify_url}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
    except Exception:
        logger.exception("Failed to send verification email to %s", user.email)


def create_password_reset_token(user: User) -> PasswordResetToken:
    with db_transaction.atomic():
        PasswordResetToken.objects.select_for_update().filter(
            user=user, used=False
        ).update(used=True)
        return PasswordResetToken.objects.create(
            user=user,
            expires_at=timezone.now() + timedelta(hours=1),
        )


def send_password_reset_email(user: User) -> None:
    token = create_password_reset_token(user)
    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token.token}"
    try:
        send_mail(
            subject="Reset your EduCore password",
            message=f"Click the link to reset your password: {reset_url}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
    except Exception:
        logger.exception("Failed to send password reset email to %s", user.email)


def initiate_password_reset(email: str) -> None:
    try:
        user = User.objects.get(email=email, is_active=True)
        send_password_reset_email(user)
    except User.DoesNotExist:
        # Silent — don't reveal whether email exists
        pass


def complete_password_reset(reset_token: PasswordResetToken, new_password: str) -> None:
    with db_transaction.atomic():
        user = reset_token.user
        user.set_password(new_password)
        user.save(update_fields=["password"])
        reset_token.used = True
        reset_token.save(update_fields=["used"])
    logger.info("Password reset completed for user %s", user.email)
