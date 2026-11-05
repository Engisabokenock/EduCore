"""
ORM model registry.

Importing this package registers every mapped class on ``Base.metadata`` so that
string-based relationships ("User", "SubscriptionPlan", ...) always resolve and
Alembic sees the complete schema.
"""
from app.models import (  # noqa: F401
    activity,
    analytics,
    asset,
    base,
    cbc,
    download,
    grade,
    notification,
    payment,
    resource,
    review,
    school,
    subject,
    subscription,
    topic,
    tracking,
)
