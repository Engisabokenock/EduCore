"""
Performance utilities: query optimization, compression, cache keys.
"""
import gzip
import io
import logging
from typing import Any, Dict, Optional

from django.conf import settings
from django.db.models import QuerySet, Prefetch

logger = logging.getLogger(__name__)


def optimize_content_queryset(queryset: QuerySet) -> QuerySet:
    return queryset.select_related(
        "grade", "subject", "topic", "author",
    ).only(
        "id", "title", "slug", "description", "resource_type",
        "grade__id", "grade__name", "grade__slug", "grade__code", "grade__curriculum",
        "subject__id", "subject__name", "subject__slug",
        "topic__id", "topic__name", "topic__slug",
        "is_premium", "file_size", "file_type", "thumbnail", "download_count",
        "view_count", "is_published", "created_at", "updated_at",
    )


def optimize_grade_queryset(queryset: QuerySet) -> QuerySet:
    return queryset.prefetch_related(
        Prefetch(
            "subjects",
            queryset=queryset.model._meta.get_field("subjects")
            .related_model.objects.filter(is_active=True)
            .only("id", "name", "slug", "grade_id", "order", "icon", "color"),
        ),
        Prefetch(
            "topics",
            queryset=queryset.model._meta.get_field("subjects")
            .related_model._meta.get_field("topics")
            .related_model.objects.filter(is_active=True)
            .only("id", "name", "slug", "subject_id", "order"),
        ),
    ).only(
        "id", "name", "slug", "code", "curriculum", "order",
    )


def gzip_response(content: bytes, level: int = 6) -> bytes:
    """Compress bytes with gzip (level 6 = good balance)."""
    buf = io.BytesIO()
    with gzip.GzipFile(fileobj=buf, mode="wb", compresslevel=level) as f:
        f.write(content)
    return buf.getvalue()


def get_compression_threshold() -> int:
    return getattr(settings, "API_RESPONSE_COMPRESSION_THRESHOLD", 500)
