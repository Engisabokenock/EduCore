import logging
from urllib.parse import quote

from app.core.config import settings

logger = logging.getLogger("educore.email")


def _frontend_link(path: str, token: str) -> str:
    return f"{settings.FRONTEND_URL.rstrip('/')}{path}?token={quote(token)}"


class AsyncEmailEngine:
    """
    Transactional e-mail dispatcher.

    Delivery is currently logged only. Plug a provider (Amazon SES, SendGrid, Resend,
    Mailgun) into ``_deliver``; the callers and link generation are production-ready.
    """

    @staticmethod
    async def _deliver(to: str, subject: str, body: str) -> None:
        if settings.is_production:
            logger.warning("E-mail provider not configured; message to %s was not delivered: %s", to, subject)
        else:
            logger.info("[DEV E-MAIL] to=%s subject=%s\n%s", to, subject, body)

    @classmethod
    async def send_verification_email(cls, email: str, token: str) -> None:
        link = _frontend_link("/verify-email", token)
        await cls._deliver(email, "Verify your EduCore account", f"Confirm your e-mail address: {link}")

    @classmethod
    async def send_application_received(cls, email: str, role_label: str) -> None:
        await cls._deliver(
            email,
            f"Your EduCore {role_label} application was received",
            f"Thanks for applying for a {role_label} account. We will e-mail you once it has been reviewed.",
        )

    @classmethod
    async def send_application_alert(cls, approver_email: str, applicant_email: str, role_label: str) -> None:
        link = f"{settings.FRONTEND_URL.rstrip('/')}/admin/approvals"
        await cls._deliver(
            approver_email,
            f"New {role_label} application on EduCore",
            f"{applicant_email} applied for a {role_label} account. Review it here: {link}",
        )

    @classmethod
    async def send_account_review_result(cls, email: str, role_label: str, *, approved: bool,
                                         note: str | None = None) -> None:
        if approved:
            link = f"{settings.FRONTEND_URL.rstrip('/')}/login"
            await cls._deliver(
                email,
                f"Your EduCore {role_label} account is approved",
                f"Your {role_label} account has been approved. Sign in here: {link}",
            )
        else:
            reason = f"\nReason: {note}" if note else ""
            await cls._deliver(
                email,
                f"Your EduCore {role_label} application",
                f"Unfortunately your {role_label} application was not approved.{reason}",
            )

    @classmethod
    async def send_password_reset_email(cls, email: str, token: str) -> None:
        link = _frontend_link("/reset-password", token)
        await cls._deliver(
            email,
            "Reset your EduCore password",
            f"Reset your password (valid {settings.PASSWORD_RESET_TOKEN_TTL_MINUTES} minutes): {link}",
        )
