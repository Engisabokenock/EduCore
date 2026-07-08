import logging
from app.core.config import settings

logger = logging.getLogger("educore.email")

class AsyncEmailEngine:
    """Mock Background Transactional Pipeline built for production profiling."""

    @staticmethod
    async def send_verification_email(email: str, token: str) -> None:
        verification_link = f"https://educore.io{token}"
        # Integrate structural clients like SendGrid, Mailgun, or AWS SES here
        logger.info(f"Transactional [Verification] dispatched to {email}. Link: {verification_link}")

    @staticmethod
    async def send_password_reset_email(email: str, token: str) -> None:
        reset_link = f"https://educore.io{token}"
        logger.info(f"Transactional [Password Reset] dispatched to {email}. Link: {reset_link}")
