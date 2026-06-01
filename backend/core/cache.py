"""
Caching utilities and decorators for high-performance content delivery.
"""
import functools
import hashlib
import json
import logging
from typing import Any, Callable

from django.conf import settings
from django.core.cache import cache
from django.db.models import QuerySet

logger = logging.getLogger(__name__)


def cache_key(*parts: str, prefix: str = "educore") -> str:
    return f"{prefix}:" + ":".join(str(p) for p in parts if p)


def cache_page(timeout: int = 300, key_prefix: str = "page") -> Callable:
    """Decorator: cache the return value of a view function for `timeout` seconds."""
    def decorator(view_func: Callable) -> Callable:
        @functools.wraps(view_func)
        def wrapper(*args, **kwargs):
            key = cache_key(key_prefix, view_func.__name__, *sorted(kwargs.items()))
            cached = cache.get(key)
            if cached is not None:
                return cached
            result = view_func(*args, **kwargs)
            try:
                cache.set(key, result, timeout)
            except Exception:
                logger.warning("Cache set failed for key %s", key)
            return result
        return wrapper
    return decorator


def cache_queryset(queryset: QuerySet, key: str, timeout: int = 300) -> QuerySet:
    """Cache a queryset result as a list to avoid repeated DB hits."""
    cache_key_name = cache_key("qs", key)
    cached = cache.get(cache_key_name)
    if cached is not None:
        return queryset.model.objects.filter(pk__in=[item.pk for item in cached])
    result = list(queryset)
    try:
        cache.set(cache_key_name, result, timeout)
    except Exception:
        logger.warning("Cache set failed for queryset %s", cache_key_name)
    return queryset


def invalidate_cache(*patterns: str) -> None:
    """Invalidate cache keys matching any of the given patterns."""
    for pattern in patterns:
        try:
            cache.delete_pattern(cache_key(pattern, "*"))
        except Exception:
            logger.warning("Cache invalidation failed for pattern %s", pattern)


def get_content_cache_key(resource_type: str, grade: str, subject: str, premium: bool) -> str:
    return cache_key(
        "content",
        resource_type,
        grade or "all",
        subject or "all",
        "premium" if premium else "free",
    )


def get_resource_detail_cache_key(slug: str) -> str:
    return cache_key("resource", "detail", slug)


def get_grade_tree_cache_key(grade_slug: str) -> str:
    return cache_key("grade", "tree", grade_slug)
