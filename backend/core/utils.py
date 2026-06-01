"""Shared utility functions."""
import re
import uuid
from django.utils.text import slugify


def generate_unique_slug(model_class, title, slug_field="slug"):
    slug = slugify(title)
    unique_slug = slug
    num = 1
    while model_class.objects.filter(**{slug_field: unique_slug}).exists():
        unique_slug = f"{slug}-{num}"
        num += 1
    return unique_slug


def generate_reference_code(prefix="EDU"):
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"


def sanitize_phone(phone: str) -> str:
    """Normalize phone to international format (254XXXXXXXXX for Kenya)."""
    digits = re.sub(r"\D", "", phone)
    if digits.startswith("0") and len(digits) == 10:
        return "254" + digits[1:]
    if digits.startswith("254") and len(digits) == 12:
        return digits
    return digits


def build_api_response(data=None, message="", errors=None, status="success"):
    return {
        "status": status,
        "message": message,
        "data": data,
        "errors": errors,
    }
