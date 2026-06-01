"""Notification delivery logic."""
import logging
from django.utils import timezone
from .models import Notification

logger = logging.getLogger("apps.notifications")


def send_notification(user, notification_type: str, title: str, body: str, channel: str = "in_app", data: dict = None) -> Notification:
    notification = Notification.objects.create(
        user=user,
        notification_type=notification_type,
        channel=channel,
        title=title,
        body=body,
        data=data or {},
        sent_at=timezone.now(),
    )
    return notification


def mark_all_read(user) -> int:
    now = timezone.now()
    return Notification.objects.filter(user=user, is_read=False).update(is_read=True, read_at=now)
