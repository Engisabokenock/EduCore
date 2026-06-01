"""Analytics business logic."""
import logging
from django.utils import timezone
from .models import Event

logger = logging.getLogger("apps.analytics")


def track_event(event_type: str, user=None, data: dict = None, request=None) -> None:
    try:
        ip = None
        user_agent = ""
        session_id = ""
        if request:
            ip = request.META.get("HTTP_X_FORWARDED_FOR", request.META.get("REMOTE_ADDR"))
            if ip and "," in ip:
                ip = ip.split(",")[0].strip()
            user_agent = request.META.get("HTTP_USER_AGENT", "")
            session_id = request.session.session_key or ""

        Event.objects.create(
            user=user if user and getattr(user, "is_authenticated", False) else None,
            event_type=event_type,
            data=data or {},
            session_id=session_id,
            ip_address=ip,
            user_agent=user_agent,
        )
    except Exception:
        logger.exception("Failed to track event: %s", event_type)
