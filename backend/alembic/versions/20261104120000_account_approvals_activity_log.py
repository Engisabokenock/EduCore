"""Account approvals and the platform activity log.

* ``users.approval_status`` (+ reviewer columns): teachers and administrators sign up
  as *pending* and cannot sign in until reviewed. Existing accounts are approved.
* ``activity_logs``: append-only record of sign-ins, approvals, staff actions,
  payments, downloads and every other state-changing API call, for the Super Admin.
* ``notificationevent`` gains ``account_review``.

Idempotent and safe to run on databases at any earlier state of this branch.

Revision ID: 20261104120000
Revises: 20261104090000
Create Date: 2026-11-04T12:00:00+00:00
"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text

revision: str = "20261104120000"
down_revision: Union[str, None] = "20261104090000"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

INDEXES = (
    ("ix_users_approval_status", "users", ("approval_status",)),
    ("ix_activity_logs_occurred_at", "activity_logs", ("occurred_at",)),
    ("ix_activity_logs_actor_id", "activity_logs", ("actor_id",)),
    ("ix_activity_logs_action", "activity_logs", ("action",)),
    ("ix_activity_logs_category_time", "activity_logs", ("category", "occurred_at")),
    ("ix_activity_logs_actor_time", "activity_logs", ("actor_id", "occurred_at")),
)


def _exec(sql: str) -> None:
    op.get_bind().execute(text(sql))


def upgrade() -> None:
    _exec(
        """
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'accountapprovalstatus') THEN
                CREATE TYPE accountapprovalstatus AS ENUM ('approved', 'pending', 'rejected');
            END IF;
        END $$;
        """
    )
    # PostgreSQL 12+ allows this inside a transaction (the value is not used here).
    _exec("ALTER TYPE notificationevent ADD VALUE IF NOT EXISTS 'account_review'")

    _exec(
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS approval_status accountapprovalstatus "
        "NOT NULL DEFAULT 'approved'"
    )
    _exec(
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS reviewed_by_id UUID "
        "REFERENCES users (id) ON DELETE SET NULL"
    )
    _exec("ALTER TABLE users ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMP WITH TIME ZONE")
    _exec("ALTER TABLE users ADD COLUMN IF NOT EXISTS review_note VARCHAR(500)")

    _exec(
        """
        CREATE TABLE IF NOT EXISTS activity_logs (
            id UUID NOT NULL PRIMARY KEY,
            occurred_at TIMESTAMP WITH TIME ZONE NOT NULL,
            actor_id UUID REFERENCES users (id) ON DELETE SET NULL,
            actor_email VARCHAR(255),
            actor_role VARCHAR(50),
            category VARCHAR(40) NOT NULL,
            action VARCHAR(80) NOT NULL,
            summary VARCHAR(500) NOT NULL,
            target_type VARCHAR(50),
            target_id VARCHAR(64),
            details JSONB NOT NULL DEFAULT '{}'::jsonb,
            ip_address VARCHAR(45),
            user_agent VARCHAR(255),
            request_id VARCHAR(64),
            http_method VARCHAR(10),
            path VARCHAR(255),
            status_code INTEGER
        )
        """
    )
    for name, table, columns in INDEXES:
        cols = ", ".join(f'"{c}"' for c in columns)
        _exec(f"CREATE INDEX IF NOT EXISTS {name} ON {table} ({cols})")


def downgrade() -> None:
    for name, _table, _columns in reversed(INDEXES):
        _exec(f"DROP INDEX IF EXISTS {name}")
    _exec("DROP TABLE IF EXISTS activity_logs")
    for column in ("review_note", "reviewed_at", "reviewed_by_id", "approval_status"):
        _exec(f"ALTER TABLE users DROP COLUMN IF EXISTS {column}")
    _exec("DROP TYPE IF EXISTS accountapprovalstatus")
    # PostgreSQL cannot drop a single enum value; 'account_review' stays (harmless).
