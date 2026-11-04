"""Schema hardening: enum labels, missing columns/tables, indexes and RBAC seed data.

The initial snapshot migration was generated with ``CreateTable`` only, which:

* never created any of the ``index=True`` / ``unique=True`` indexes (so e-mail
  addresses, slugs and M-Pesa receipt numbers were not actually unique),
* skipped the ``portal_resources`` table entirely,
* pre-dated the user verification / password-reset columns the API relies on.

This revision repairs an existing database in place and is safe to run on a fresh
one. Every step is idempotent.

Revision ID: 20261104090000
Revises: 20260710121842
Create Date: 2026-11-04T09:00:00+00:00
"""
import logging
import uuid
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text

revision: str = "20261104090000"
down_revision: Union[str, None] = "20260710121842"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

log = logging.getLogger("alembic.runtime.migration")

# ---------------------------------------------------------------------------
# Static snapshots (migrations must not import application code).
# ---------------------------------------------------------------------------

# enum type -> {MEMBER_NAME: value}. Databases created via ``create_all`` before the
# enum fix stored member names; rename those labels to the values the ORM now writes.
ENUM_LABELS = {
    "dynamicpermission": {
        "MANAGE_ADMINS": "manage_admins", "MANAGE_SECURITY": "manage_security",
        "MANAGE_SYSTEM": "manage_system", "VIEW_AUDIT_LOGS": "view_audit_logs",
        "MANAGE_ROLES": "manage_roles", "MANAGE_USERS": "manage_users",
        "MANAGE_RESOURCES": "manage_resources", "MANAGE_PAYMENTS": "manage_payments",
        "MANAGE_REVIEWS": "manage_reviews", "MANAGE_NOTIFICATIONS": "manage_notifications",
        "MANAGE_MARKETING": "manage_marketing", "MANAGE_REPORTS": "manage_reports",
        "MANAGE_SCHOOLS": "manage_schools", "MANAGE_TEACHERS": "manage_teachers",
        "MANAGE_STUDENTS": "manage_students", "MANAGE_SUBSCRIPTIONS": "manage_subscriptions",
        "MANAGE_AI": "manage_ai", "MANAGE_SETTINGS": "manage_settings",
    },
    "plantier": {"WEEKLY": "weekly", "MONTHLY": "monthly", "QUARTERLY": "quarterly", "YEARLY": "yearly"},
    "notificationevent": {
        "PAYMENT_SUCCESS": "payment_success", "NEW_RESOURCE": "new_resource",
        "SUBSCRIPTION_EXPIRY": "subscription_expiry", "PASSWORD_RESET": "password_reset",
        "WELCOME": "welcome",
    },
    "notificationchannel": {"EMAIL": "email", "SMS": "sms", "WHATSAPP": "whatsapp", "PUSH": "push"},
    "subscriptionstate": {
        "ACTIVE": "active", "CANCELED": "canceled", "GRACE_PERIOD": "grace_period", "EXPIRED": "expired",
    },
    "academicterm": {"TERM_1": "1", "TERM_2": "2", "TERM_3": "3"},
    "resourcetypevariant": {
        "REVISION_PAPER": "revision_paper", "WORKSHEET": "worksheet", "EXAM": "exam",
        "MOCK_EXAM": "mock_exam", "PAST_PAPER": "past_paper", "LESSON_NOTE": "lesson_note",
        "MARKING_SCHEME": "marking_scheme", "SCHEME_OF_WORK": "scheme_of_work",
        "LESSON_PLAN": "lesson_plan",
    },
    "resourcetype": {"DOCUMENT": "document", "VIDEO": "video", "AUDIO": "audio", "INTERACTIVE": "interactive"},
    "assignmentstatus": {"PENDING": "pending", "SUBMITTED": "submitted", "GRADED": "graded"},
    "reviewmoderationstatus": {"PENDING": "pending", "APPROVED": "approved", "REJECTED": "rejected"},
}

NEW_ENUMS = {
    "extendedresourcetype": [
        "exam", "note", "worksheet", "quiz", "past_paper", "marking_scheme", "lesson_plan",
        "scheme_of_work", "assignment", "holiday_assignment", "revision_paper", "video",
        "audio", "presentation", "other",
    ],
    "workflowapprovalstate": ["draft", "pending_review", "approved", "rejected", "published"],
    "assetvisibilityscope": ["public", "registered", "premium", "private", "school"],
}

# (name, table, columns, unique)
INDEXES = [
    ("ix_cbc_grades_code", "cbc_grades", ["code"], True),
    ("ix_cbc_grades_name", "cbc_grades", ["name"], True),
    ("ix_cbc_grades_slug", "cbc_grades", ["slug"], True),
    ("ix_content_tags_name", "content_tags", ["name"], True),
    ("ix_permissions_name", "permissions", ["name"], True),
    ("ix_roles_name", "roles", ["name"], True),
    ("ix_schools_name", "schools", ["name"], True),
    ("ix_schools_registration_code", "schools", ["registration_code"], True),
    ("ix_subscription_plans_name", "subscription_plans", ["name"], True),
    ("ix_cbc_subjects_code", "cbc_subjects", ["code"], True),
    ("ix_cbc_subjects_name", "cbc_subjects", ["name"], False),
    ("ix_cbc_subjects_slug", "cbc_subjects", ["slug"], False),
    ("ux_cbc_subjects_grade_slug", "cbc_subjects", ["grade_id", "slug"], True),
    ("ix_users_email", "users", ["email"], True),
    ("ix_users_reset_token", "users", ["reset_token"], False),
    ("ix_users_verification_token", "users", ["verification_token"], False),
    ("ix_cbc_topics_name", "cbc_topics", ["name"], False),
    ("ix_cbc_topics_slug", "cbc_topics", ["slug"], False),
    ("ux_cbc_topics_subject_slug", "cbc_topics", ["subject_id", "slug"], True),
    ("ix_classrooms_academic_year", "classrooms", ["academic_year"], False),
    ("ux_school_grade_stream_year", "classrooms", ["school_id", "grade_id", "stream_name", "academic_year"], True),
    ("ix_notification_logs_event_type", "notification_logs", ["event_type"], False),
    ("ix_notification_logs_is_read", "notification_logs", ["is_read"], False),
    ("ix_notification_logs_sent_at", "notification_logs", ["sent_at"], False),
    ("ix_notification_logs_user_id", "notification_logs", ["user_id"], False),
    ("ix_notification_preferences_user_id", "notification_preferences", ["user_id"], False),
    ("ux_user_event_channel", "notification_preferences", ["user_id", "event_type", "channel"], True),
    ("ix_payment_transactions_checkout_request_id", "payment_transactions", ["checkout_request_id"], True),
    ("ix_payment_transactions_merchant_request_id", "payment_transactions", ["merchant_request_id"], True),
    ("ix_payment_transactions_mpesa_receipt_number", "payment_transactions", ["mpesa_receipt_number"], True),
    ("ix_payment_transactions_user_id", "payment_transactions", ["user_id"], False),
    ("ix_user_sessions_refresh_token", "user_sessions", ["refresh_token"], True),
    ("ix_user_subs_lifecycle", "user_subscriptions", ["status", "current_period_end"], False),
    ("ix_user_subscriptions_status", "user_subscriptions", ["status"], False),
    ("ix_academic_resources_is_published", "academic_resources", ["is_published"], False),
    ("ix_academic_resources_slug", "academic_resources", ["slug"], True),
    ("ix_academic_resources_title", "academic_resources", ["title"], False),
    ("ix_academic_resources_type_variant", "academic_resources", ["type_variant"], False),
    ("ix_academic_resources_year", "academic_resources", ["year"], False),
    ("ix_academic_resources_catalog", "academic_resources", ["grade_id", "subject_id", "topic_id", "is_published"], False),
    ("ix_cbc_learning_outcomes_code", "cbc_learning_outcomes", ["code"], True),
    ("ux_classroom_student", "classroom_enrollments", ["classroom_id", "student_id"], True),
    ("ix_portal_resources_approval_state", "portal_resources", ["approval_state"], False),
    ("ix_portal_resources_category", "portal_resources", ["category"], False),
    ("ix_portal_resources_title", "portal_resources", ["title"], False),
    ("ix_resources_permission_lookup", "portal_resources", ["approval_state", "visibility", "owner_id"], False),
    ("ux_assignment_student", "assignment_submissions", ["assignment_id", "student_id"], True),
    ("ix_download_logs_downloaded_at", "download_logs", ["downloaded_at"], False),
    ("ix_downloads_resource_timeline", "download_logs", ["resource_id", "downloaded_at"], False),
    ("ix_downloads_user_timeline", "download_logs", ["user_id", "downloaded_at"], False),
    ("ix_downloads_ip_timeline", "download_logs", ["ip_address", "downloaded_at"], False),
    ("ix_resource_reviews_is_reported", "resource_reviews", ["is_reported"], False),
    ("ix_resource_reviews_moderation_status", "resource_reviews", ["moderation_status"], False),
    ("ux_user_resource_review", "resource_reviews", ["user_id", "resource_id"], True),
]

ALL_PERMISSIONS = list(ENUM_LABELS["dynamicpermission"].values())
PLATFORM_ONLY = {"manage_admins", "manage_security", "manage_system", "view_audit_logs", "manage_roles"}
ROLE_PERMISSIONS = {
    "super_admin": ALL_PERMISSIONS,
    "admin": [p for p in ALL_PERMISSIONS if p not in PLATFORM_ONLY],
    "school_admin": ["manage_teachers", "manage_students", "manage_reports"],
    "teacher": ["manage_resources"],
    "parent": [],
    "student": [],
}


def _exec(sql: str, **params) -> None:
    op.get_bind().execute(text(sql), params)


def _scalar(sql: str, **params):
    return op.get_bind().execute(text(sql), params).scalar()


def _normalize_enum_labels() -> None:
    for type_name, mapping in ENUM_LABELS.items():
        for member_name, value in mapping.items():
            _exec(
                f"""
                DO $$ BEGIN
                    IF EXISTS (
                        SELECT 1 FROM pg_enum e JOIN pg_type t ON t.oid = e.enumtypid
                        WHERE t.typname = '{type_name}' AND e.enumlabel = '{member_name}'
                    ) AND NOT EXISTS (
                        SELECT 1 FROM pg_enum e JOIN pg_type t ON t.oid = e.enumtypid
                        WHERE t.typname = '{type_name}' AND e.enumlabel = '{value}'
                    ) THEN
                        ALTER TYPE {type_name} RENAME VALUE '{member_name}' TO '{value}';
                    END IF;
                END $$;
                """
            )


def _create_enum_types() -> None:
    for type_name, values in NEW_ENUMS.items():
        labels = ", ".join(f"'{v}'" for v in values)
        _exec(
            f"""
            DO $$ BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = '{type_name}') THEN
                    CREATE TYPE {type_name} AS ENUM ({labels});
                END IF;
            END $$;
            """
        )


def _add_columns() -> None:
    _exec("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_verified BOOLEAN NOT NULL DEFAULT false")
    _exec("ALTER TABLE users ADD COLUMN IF NOT EXISTS verification_token VARCHAR(128)")
    _exec("ALTER TABLE users ADD COLUMN IF NOT EXISTS reset_token VARCHAR(128)")
    _exec("ALTER TABLE users ADD COLUMN IF NOT EXISTS reset_token_expires TIMESTAMP WITH TIME ZONE")
    _exec("ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login_at TIMESTAMP WITH TIME ZONE")

    _exec(
        "ALTER TABLE payment_transactions ADD COLUMN IF NOT EXISTS plan_id UUID "
        "REFERENCES subscription_plans (id) ON DELETE SET NULL"
    )
    _exec("ALTER TABLE payment_transactions ADD COLUMN IF NOT EXISTS account_reference VARCHAR(20)")


def _create_portal_resources() -> None:
    _exec(
        """
        CREATE TABLE IF NOT EXISTS portal_resources (
            id UUID NOT NULL PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            description TEXT,
            category extendedresourcetype NOT NULL,
            grade_id UUID NOT NULL REFERENCES cbc_grades (id) ON DELETE RESTRICT,
            subject_id UUID NOT NULL REFERENCES cbc_subjects (id) ON DELETE RESTRICT,
            topic_id UUID REFERENCES cbc_topics (id) ON DELETE SET NULL,
            school_id UUID REFERENCES schools (id) ON DELETE SET NULL,
            file_url VARCHAR(512) NOT NULL,
            file_extension VARCHAR(10) NOT NULL,
            is_free BOOLEAN NOT NULL,
            price NUMERIC(10, 2) NOT NULL,
            requires_subscription BOOLEAN NOT NULL,
            visibility assetvisibilityscope NOT NULL,
            approval_state workflowapprovalstate NOT NULL,
            owner_id UUID NOT NULL REFERENCES users (id) ON DELETE RESTRICT,
            created_at TIMESTAMP WITH TIME ZONE,
            updated_at TIMESTAMP WITH TIME ZONE
        )
        """
    )


def _repair_data() -> None:
    # E-mail addresses are case-insensitive identities; the API now lowercases them.
    _exec(
        """
        UPDATE users u SET email = lower(u.email)
        WHERE u.email <> lower(u.email)
          AND NOT EXISTS (SELECT 1 FROM users o WHERE o.id <> u.id AND o.email = lower(u.email))
        """
    )
    # Earlier seeds produced colliding subject codes (e.g. "G1-CRE" for both
    # "CRE / IRE" and "Creative Arts"). Suffix duplicates so the unique index holds.
    _exec(
        """
        UPDATE cbc_subjects s SET code = left(s.code, 24) || '-' || left(s.id::text, 5)
        FROM (
            SELECT id, row_number() OVER (PARTITION BY code ORDER BY "order", id) AS rn
            FROM cbc_subjects
        ) d
        WHERE d.id = s.id AND d.rn > 1
        """
    )
    # Roles created by an older register flow may have been stored as "UserRole.X".
    _exec(
        """
        UPDATE roles r SET name = lower(substring(r.name from 10))
        WHERE r.name LIKE 'UserRole.%'
          AND NOT EXISTS (SELECT 1 FROM roles o WHERE o.name = lower(substring(r.name from 10)))
        """
    )


def _create_indexes() -> None:
    for name, table, columns, unique in INDEXES:
        cols = ", ".join(f'"{c}"' for c in columns)
        if unique:
            not_null = " AND ".join(f'"{c}" IS NOT NULL' for c in columns)
            duplicate = _scalar(
                f"SELECT 1 FROM {table} WHERE {not_null} GROUP BY {cols} HAVING count(*) > 1 LIMIT 1"
            )
            if duplicate:
                log.warning(
                    "Skipping unique index %s on %s(%s): duplicate rows exist. "
                    "De-duplicate the data and re-run the migration.", name, table, cols,
                )
                continue
        kind = "UNIQUE INDEX" if unique else "INDEX"
        _exec(f"CREATE {kind} IF NOT EXISTS {name} ON {table} ({cols})")


def _seed_rbac() -> None:
    for perm in ALL_PERMISSIONS:
        _exec(
            "INSERT INTO permissions (id, name, description) "
            "SELECT CAST(:id AS uuid), CAST(:name AS dynamicpermission), CAST(:description AS varchar) "
            "WHERE NOT EXISTS (SELECT 1 FROM permissions WHERE name = CAST(:name AS dynamicpermission))",
            id=uuid.uuid4(), name=perm, description=perm.replace("_", " ").capitalize(),
        )
    for role, perms in ROLE_PERMISSIONS.items():
        _exec(
            "INSERT INTO roles (id, name) SELECT CAST(:id AS uuid), CAST(:name AS varchar) "
            "WHERE NOT EXISTS (SELECT 1 FROM roles WHERE name = CAST(:name AS varchar))",
            id=uuid.uuid4(), name=role,
        )
        for perm in perms:
            _exec(
                """
                INSERT INTO role_permissions (role_id, permission_id)
                SELECT r.id, p.id FROM roles r, permissions p
                WHERE r.name = CAST(:role AS varchar) AND p.name = CAST(:perm AS dynamicpermission)
                ON CONFLICT DO NOTHING
                """,
                role=role, perm=perm,
            )


def upgrade() -> None:
    _normalize_enum_labels()
    _create_enum_types()
    _add_columns()
    _create_portal_resources()
    _repair_data()
    _create_indexes()
    _seed_rbac()


def downgrade() -> None:
    for name, _table, _cols, _unique in reversed(INDEXES):
        _exec(f"DROP INDEX IF EXISTS {name}")
    _exec("DROP TABLE IF EXISTS portal_resources")
    _exec("ALTER TABLE payment_transactions DROP COLUMN IF EXISTS account_reference")
    _exec("ALTER TABLE payment_transactions DROP COLUMN IF EXISTS plan_id")
    for column in ("last_login_at", "reset_token_expires", "reset_token", "verification_token", "is_verified"):
        _exec(f"ALTER TABLE users DROP COLUMN IF EXISTS {column}")
    for type_name in NEW_ENUMS:
        _exec(f"DROP TYPE IF EXISTS {type_name}")
