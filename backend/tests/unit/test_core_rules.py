"""Pure unit tests for business rules (no database required)."""
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from app.core.security import (
    create_jwt_token,
    hash_token,
    safe_filename,
    verify_jwt_token,
    verify_password,
)
from app.core.exceptions import AuthenticationError
from app.models.subscription import SubscriptionState
from app.schemas.payment import normalize_kenyan_msisdn
from app.services.subscription_service import subscription_grants_access
from app.utils.text import escape_like, slugify


@pytest.mark.parametrize("raw,expected", [
    ("0712345678", "254712345678"),
    ("0112345678", "254112345678"),
    ("712345678", "254712345678"),
    ("+254 712 345 678", "254712345678"),
    ("254712345678", "254712345678"),
])
def test_phone_normalization(raw, expected):
    assert normalize_kenyan_msisdn(raw) == expected


@pytest.mark.parametrize("raw", ["0812345678", "12345", "2547123456789", ""])
def test_phone_rejects_invalid(raw):
    with pytest.raises(ValueError):
        normalize_kenyan_msisdn(raw)


def _sub(status, end_delta_days, grace_delta_days=None):
    now = datetime.now(timezone.utc)
    return SimpleNamespace(
        status=status,
        current_period_end=now + timedelta(days=end_delta_days),
        grace_period_end=None if grace_delta_days is None else now + timedelta(days=grace_delta_days),
    )


def test_subscription_access_rules():
    assert subscription_grants_access(_sub(SubscriptionState.ACTIVE, 5))
    assert subscription_grants_access(_sub(SubscriptionState.CANCELED, 5))  # paid until period end
    assert not subscription_grants_access(_sub(SubscriptionState.ACTIVE, -1))
    assert subscription_grants_access(_sub(SubscriptionState.GRACE_PERIOD, -1, 2))
    assert not subscription_grants_access(_sub(SubscriptionState.GRACE_PERIOD, -5, -1))
    assert not subscription_grants_access(_sub(SubscriptionState.EXPIRED, 30))
    assert not subscription_grants_access(None)


def test_tokens_are_unique_and_typed():
    a = create_jwt_token("8f8e8d8c-0000-4000-8000-000000000000", timedelta(minutes=5), is_refresh=True)
    b = create_jwt_token("8f8e8d8c-0000-4000-8000-000000000000", timedelta(minutes=5), is_refresh=True)
    assert a != b  # jti prevents identical tokens within the same second
    assert verify_jwt_token(a, is_refresh=True)["type"] == "refresh"
    with pytest.raises(AuthenticationError):
        verify_jwt_token(a, is_refresh=False)  # refresh token cannot be used as an access token


def test_malformed_password_hash_fails_closed():
    assert verify_password("anything", "not-a-real-hash") is False


def test_helpers():
    assert slugify("CRE / IRE") == "cre-ire"
    assert escape_like("100%_x") == "100\\%\\_x"
    assert safe_filename("../../etc/passwd") == "passwd"
    assert len(hash_token("abc")) == 64
