import logging
import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_
from app.models.base import User
from app.models.notification import NotificationChannel, NotificationEvent, NotificationPreference, NotificationLog

logger = logging.getLogger("educore.notifications")

class CoreNotificationEngine:
    """Production messaging engine with strict preferences checking and mock provider execution lines."""

    @staticmethod
    async def _channel_is_allowed(user_id: uuid.UUID, event: NotificationEvent, channel: NotificationChannel, db: AsyncSession) -> bool:
        """Asserts user configuration flags across privacy grids before launching transport requests."""
        stmt = select(NotificationPreference.is_enabled).where(
            and_(
                NotificationPreference.user_id == user_id,
                NotificationPreference.event_type == event,
                NotificationPreference.channel == channel
            )
        )
        res = await db.execute(stmt)
        allowed_flag = res.scalar()
        return allowed_flag if allowed_flag is not None else True # Default to open delivery channels

    @classmethod
    async def dispatch(
        cls,
        user: User,
        event: NotificationEvent,
        channels: list[NotificationChannel],
        title: str,
        body: str,
        db: AsyncSession
    ) -> None:
        """Routes transaction dispatches across delivery arrays dynamically based on opt-in states."""
        for channel in channels:
            if not await cls._channel_is_allowed(user.id, event, channel, db):
                logger.info(f"Skipping dispatch for User {user.id}. Channel {channel.value} is muted for {event.value}")
                continue

            recipient = user.email if channel == NotificationChannel.EMAIL else user.profile.phone_number
            if not recipient:
                logger.warning(f"Aborted routing loop. Recipient profile address missing for channel target: {channel.value}")
                continue

            log_entry = NotificationLog(
                user_id=user.id,
                event_type=event,
                channel=channel,
                recipient_address=recipient,
                title=title,
                body=body
            )

            try:
                if channel == NotificationChannel.EMAIL:
                    # Target infrastructure points like AWS SES / SendGrid here
                    logger.info(f"[EMAIL MOCK DARAJA] To: {recipient} | Subject: {title} | Body: {body[:40]}...")
                elif channel == NotificationChannel.SMS:
                    # Connect premium low-latency SMS routes (e.g., Africa's Talking)
                    logger.info(f"[SMS MOCK DARAJA] To: {recipient} | Body: {body}")
                elif channel == NotificationChannel.WHATSAPP:
                    # Route execution lines down to Meta API enterprise targets
                    logger.info(f"[WHATSAPP MOCK Enterprise] To: {recipient} | Body: {body[:40]}...")
                elif channel == NotificationChannel.PUSH:
                    # Fire base FCM message parameters payloads downstream
                    logger.info(f"[FCM PUSH MOCK Token] Target Identity: {user.id} | Title: {title}")

                log_entry.is_sent = True
            except Exception as transport_error:
                logger.error(f"Transport route breakdown tracking channel {channel.value}: {str(transport_error)}")
                log_entry.is_sent = False
                log_entry.failure_reason = str(transport_error)

            db.add(log_entry)

        await db.flush()
