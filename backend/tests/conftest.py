"""
Test configuration.

Integration tests need a disposable PostgreSQL database with migrations applied:

    export TEST_DATABASE_URL=postgresql+asyncpg://postgres:test@localhost:55432/educore_test
    alembic upgrade head        # with DATABASE_URL pointing at the same database
    pytest

They are skipped when TEST_DATABASE_URL is not set, and they never fall back to the
DATABASE_URL in .env, so a production database can't be truncated by accident.
"""
import os

import pytest

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")

# Settings are read at import time, so configure the environment before importing the app.
os.environ.setdefault("SECRET_KEY", "test-secret-key-0123456789abcdef")
os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-access-0123456789abcdef")
os.environ.setdefault("JWT_REFRESH_SECRET", "test-jwt-refresh-0123456789abcdef")
os.environ.setdefault("MPESA_CALLBACK_SECRET", "cb-secret-test")
os.environ["APP_ENV"] = "development"
os.environ["RATE_LIMIT_PER_MINUTE"] = "100000"
os.environ["AUTH_RATE_LIMIT_PER_MINUTE"] = "100000"
os.environ.setdefault("REDIS_URL", "")
if TEST_DATABASE_URL:
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL
else:
    os.environ["DATABASE_URL"] = "postgresql+asyncpg://invalid:invalid@127.0.0.1:1/never_used"

requires_db = pytest.mark.skipif(not TEST_DATABASE_URL, reason="TEST_DATABASE_URL not set")

# Tables wiped between tests. Roles/permissions (seeded by migration) are kept.
_TRUNCATE = (
    "resource_reviews, download_logs, resource_tag_associations, content_tags, academic_resources, "
    "notification_logs, notification_preferences, payment_transactions, premium_subscriptions, "
    "user_subscriptions, subscription_plans, user_sessions, profiles, portal_resources, "
    "assignment_submissions, class_assignments, classroom_enrollments, classrooms, schools, "
    "cbc_resources, cbc_learning_outcomes, cbc_topics, cbc_subjects, cbc_grades, users"
)


@pytest.fixture
async def db_engine():
    from app.core.database import engine

    yield engine
    await engine.dispose()


@pytest.fixture
async def clean_db(db_engine):
    from sqlalchemy import text

    async with db_engine.begin() as conn:
        await conn.execute(text(f"TRUNCATE {_TRUNCATE} RESTART IDENTITY CASCADE"))
    yield


@pytest.fixture
async def client(clean_db):
    import httpx

    from app.main import app

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as c:
        yield c
