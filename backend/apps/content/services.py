"""
Content business logic.
Views must NEVER contain logic — call these service functions instead.
"""
import logging
from django.conf import settings
from django.core.cache import cache
from django.db.models import F, QuerySet
from django.utils import timezone

from config.middleware import _build_signed_url

from .models import Resource, Download

logger = logging.getLogger("apps.content")


# ── Access control ────────────────────────────────────────────────────────────

def _user_is_premium(user) -> bool:
    if not user or not getattr(user, "is_authenticated", False):
        return False
    if getattr(user, "role", None) == "admin":
        return True
    return user.subscriptions.filter(status="active").exists()


def user_can_access_resource(resource: Resource, user) -> bool:
    if resource.is_free:
        return True
    return _user_is_premium(user)


def user_can_access_answer_sheet(user) -> bool:
    return _user_is_premium(user)


def get_signed_file_url(request, file_url: str) -> str | None:
    """Return a time-limited signed URL for *file_url* if the user is premium."""
    if not request or not request.user or not request.user.is_authenticated:
        return None
    if not _user_is_premium(request.user):
        return None
    path = file_url.split("?")[0]
    return _build_signed_url(path, ttl_seconds=settings.MEDIA_SIGNED_URL_TTL)


# ── Stats ─────────────────────────────────────────────────────────────────────

def record_view(resource: Resource) -> None:
    Resource.objects.filter(pk=resource.pk).update(view_count=F("view_count") + 1)


def record_download(resource: Resource, user=None, ip_address: str = None, user_agent: str = "") -> Download:
    download = Download.objects.create(
        resource=resource,
        user=user if user and getattr(user, "is_authenticated", False) else None,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    Resource.objects.filter(pk=resource.pk).update(download_count=F("download_count") + 1)
    return download


# ── Publishing ────────────────────────────────────────────────────────────────

def publish_resource(resource: Resource) -> None:
    resource.is_published = True
    resource.published_at = timezone.now()
    resource.save(update_fields=["is_published", "published_at"])


def unpublish_resource(resource: Resource) -> None:
    resource.is_published = False
    resource.save(update_fields=["is_published"])


# ── Querysets ─────────────────────────────────────────────────────────────────

def get_published_resources() -> QuerySet:
    return (
        Resource.objects.filter(is_published=True)
        .select_related("grade", "subject", "topic", "author")
        .order_by("-created_at")
    )


def get_resource_by_slug(slug: str) -> Resource:
    return Resource.objects.select_related("grade", "subject", "topic", "author").get(
        slug=slug, is_published=True
    )


def get_client_ip(request) -> str:
    ip = request.META.get("HTTP_X_FORWARDED_FOR", request.META.get("REMOTE_ADDR", ""))
    return ip.split(",")[0].strip() if "," in ip else ip
