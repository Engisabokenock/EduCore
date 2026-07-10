"""Initial schema snapshot

Revision ID: 20260710112342
Revises:
Create Date: 2026-07-10T11:23:42.998302+00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

revision: str = '20260710112342'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(text("""
    DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'dynamicpermission') THEN CREATE TYPE dynamicpermission AS ENUM ('manage_admins', 'manage_security', 'manage_system', 'view_audit_logs', 'manage_roles', 'manage_users', 'manage_resources', 'manage_payments', 'manage_reviews', 'manage_notifications', 'manage_marketing', 'manage_reports', 'manage_schools', 'manage_teachers', 'manage_students', 'manage_subscriptions', 'manage_ai', 'manage_settings'); END IF; END $$;
    DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'plantier') THEN CREATE TYPE plantier AS ENUM ('weekly', 'monthly', 'quarterly', 'yearly'); END IF; END $$;
    DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'notificationevent') THEN CREATE TYPE notificationevent AS ENUM ('payment_success', 'new_resource', 'subscription_expiry', 'password_reset', 'welcome'); END IF; END $$;
    DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'notificationchannel') THEN CREATE TYPE notificationchannel AS ENUM ('email', 'sms', 'whatsapp', 'push'); END IF; END $$;
    DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'subscriptionstate') THEN CREATE TYPE subscriptionstate AS ENUM ('active', 'canceled', 'grace_period', 'expired'); END IF; END $$;
    DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'academicterm') THEN CREATE TYPE academicterm AS ENUM ('1', '2', '3'); END IF; END $$;
    DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'resourcetypevariant') THEN CREATE TYPE resourcetypevariant AS ENUM ('revision_paper', 'worksheet', 'exam', 'mock_exam', 'past_paper', 'lesson_note', 'marking_scheme', 'scheme_of_work', 'lesson_plan'); END IF; END $$;
    DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'resourcetype') THEN CREATE TYPE resourcetype AS ENUM ('document', 'video', 'audio', 'interactive'); END IF; END $$;
    DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'assignmentstatus') THEN CREATE TYPE assignmentstatus AS ENUM ('pending', 'submitted', 'graded'); END IF; END $$;
    DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'reviewmoderationstatus') THEN CREATE TYPE reviewmoderationstatus AS ENUM ('pending', 'approved', 'rejected'); END IF; END $$;
    CREATE TABLE IF NOT EXISTS  cbc_grades (
	id UUID NOT NULL, 
	name VARCHAR(50) NOT NULL, 
	code VARCHAR(20) NOT NULL, 
	description TEXT, 
	slug VARCHAR(50) NOT NULL, 
	curriculum VARCHAR(20) NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	"order" INTEGER NOT NULL, 
	PRIMARY KEY (id)
)


    ALTER TABLE IF EXISTS cbc_grades OWNER TO postgres;
    CREATE TABLE IF NOT EXISTS  content_tags (
	id UUID NOT NULL, 
	name VARCHAR(50) NOT NULL, 
	PRIMARY KEY (id)
)


    ALTER TABLE IF EXISTS content_tags OWNER TO postgres;
    CREATE TABLE IF NOT EXISTS  permissions (
	id UUID NOT NULL, 
	name dynamicpermission NOT NULL, 
	description VARCHAR(255), 
	PRIMARY KEY (id)
)


    ALTER TABLE IF EXISTS permissions OWNER TO postgres;
    CREATE TABLE IF NOT EXISTS  roles (
	id UUID NOT NULL, 
	name VARCHAR(50) NOT NULL, 
	PRIMARY KEY (id)
)


    ALTER TABLE IF EXISTS roles OWNER TO postgres;
    CREATE TABLE IF NOT EXISTS  schools (
	id UUID NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	registration_code VARCHAR(100) NOT NULL, 
	address VARCHAR(255), 
	is_active BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)


    ALTER TABLE IF EXISTS schools OWNER TO postgres;
    CREATE TABLE IF NOT EXISTS  subscription_plans (
	id UUID NOT NULL, 
	name VARCHAR(50) NOT NULL, 
	tier plantier NOT NULL, 
	price NUMERIC(10, 2) NOT NULL, 
	duration_days INTEGER NOT NULL, 
	is_available BOOLEAN NOT NULL, 
	description VARCHAR(255), 
	features VARCHAR(1024), 
	is_featured BOOLEAN NOT NULL, 
	sort_order INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (tier)
)


    ALTER TABLE IF EXISTS subscription_plans OWNER TO postgres;
    CREATE TABLE IF NOT EXISTS  cbc_subjects (
	id UUID NOT NULL, 
	grade_id UUID NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	code VARCHAR(30) NOT NULL, 
	description TEXT, 
	slug VARCHAR(100) NOT NULL, 
	icon VARCHAR(10), 
	color VARCHAR(50), 
	is_active BOOLEAN NOT NULL, 
	"order" INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(grade_id) REFERENCES cbc_grades (id) ON DELETE CASCADE
)


    ALTER TABLE IF EXISTS cbc_subjects OWNER TO postgres;
    CREATE TABLE IF NOT EXISTS  role_permissions (
	role_id UUID NOT NULL, 
	permission_id UUID NOT NULL, 
	PRIMARY KEY (role_id, permission_id), 
	FOREIGN KEY(role_id) REFERENCES roles (id) ON DELETE CASCADE, 
	FOREIGN KEY(permission_id) REFERENCES permissions (id) ON DELETE CASCADE
)


    ALTER TABLE IF EXISTS role_permissions OWNER TO postgres;
    CREATE TABLE IF NOT EXISTS  users (
	id UUID NOT NULL, 
	email VARCHAR(255) NOT NULL, 
	hashed_password VARCHAR(255) NOT NULL, 
	role_id UUID NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(role_id) REFERENCES roles (id) ON DELETE RESTRICT
)


    ALTER TABLE IF EXISTS users OWNER TO postgres;
    CREATE TABLE IF NOT EXISTS  cbc_topics (
	id UUID NOT NULL, 
	subject_id UUID NOT NULL, 
	name VARCHAR(150) NOT NULL, 
	ordering INTEGER NOT NULL, 
	slug VARCHAR(150) NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(subject_id) REFERENCES cbc_subjects (id) ON DELETE CASCADE
)


    ALTER TABLE IF EXISTS cbc_topics OWNER TO postgres;
    CREATE TABLE IF NOT EXISTS  classrooms (
	id UUID NOT NULL, 
	school_id UUID NOT NULL, 
	grade_id UUID NOT NULL, 
	stream_name VARCHAR(50) NOT NULL, 
	academic_year INTEGER NOT NULL, 
	class_teacher_id UUID, 
	PRIMARY KEY (id), 
	FOREIGN KEY(school_id) REFERENCES schools (id) ON DELETE CASCADE, 
	FOREIGN KEY(grade_id) REFERENCES cbc_grades (id) ON DELETE RESTRICT, 
	FOREIGN KEY(class_teacher_id) REFERENCES users (id) ON DELETE SET NULL
)


    ALTER TABLE IF EXISTS classrooms OWNER TO postgres;
    CREATE TABLE IF NOT EXISTS  notification_logs (
	id UUID NOT NULL, 
	user_id UUID, 
	event_type notificationevent NOT NULL, 
	channel notificationchannel NOT NULL, 
	recipient_address VARCHAR(255) NOT NULL, 
	title VARCHAR(255) NOT NULL, 
	body TEXT NOT NULL, 
	data JSONB, 
	is_sent BOOLEAN NOT NULL, 
	is_read BOOLEAN NOT NULL, 
	read_at TIMESTAMP WITH TIME ZONE, 
	failure_reason VARCHAR(512), 
	sent_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE SET NULL
)


    ALTER TABLE IF EXISTS notification_logs OWNER TO postgres;
    CREATE TABLE IF NOT EXISTS  notification_preferences (
	id UUID NOT NULL, 
	user_id UUID NOT NULL, 
	event_type notificationevent NOT NULL, 
	channel notificationchannel NOT NULL, 
	is_enabled BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
)


    ALTER TABLE IF EXISTS notification_preferences OWNER TO postgres;
    CREATE TABLE IF NOT EXISTS  payment_transactions (
	id UUID NOT NULL, 
	user_id UUID NOT NULL, 
	amount NUMERIC(10, 2) NOT NULL, 
	phone_number VARCHAR(15) NOT NULL, 
	status VARCHAR NOT NULL, 
	merchant_request_id VARCHAR(100) NOT NULL, 
	checkout_request_id VARCHAR(100) NOT NULL, 
	mpesa_receipt_number VARCHAR(50), 
	raw_callback_payload JSON, 
	failure_reason VARCHAR(255), 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE RESTRICT
)


    ALTER TABLE IF EXISTS payment_transactions OWNER TO postgres;
    CREATE TABLE IF NOT EXISTS  premium_subscriptions (
	id UUID NOT NULL, 
	user_id UUID NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	expires_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (user_id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
)


    ALTER TABLE IF EXISTS premium_subscriptions OWNER TO postgres;
    CREATE TABLE IF NOT EXISTS  profiles (
	id UUID NOT NULL, 
	user_id UUID NOT NULL, 
	full_name VARCHAR(100) NOT NULL, 
	avatar_url VARCHAR(512), 
	phone_number VARCHAR(30), 
	metadata_fields JSONB NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (user_id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
)


    ALTER TABLE IF EXISTS profiles OWNER TO postgres;
    CREATE TABLE IF NOT EXISTS  user_sessions (
	id UUID NOT NULL, 
	user_id UUID NOT NULL, 
	refresh_token VARCHAR(512) NOT NULL, 
	user_agent VARCHAR(255), 
	ip_address VARCHAR(45), 
	is_revoked BOOLEAN NOT NULL, 
	expires_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
)


    ALTER TABLE IF EXISTS user_sessions OWNER TO postgres;
    CREATE TABLE IF NOT EXISTS  user_subscriptions (
	id UUID NOT NULL, 
	user_id UUID NOT NULL, 
	plan_id UUID NOT NULL, 
	status subscriptionstate NOT NULL, 
	auto_renew BOOLEAN NOT NULL, 
	current_period_start TIMESTAMP WITH TIME ZONE NOT NULL, 
	current_period_end TIMESTAMP WITH TIME ZONE NOT NULL, 
	grace_period_end TIMESTAMP WITH TIME ZONE, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (user_id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
	FOREIGN KEY(plan_id) REFERENCES subscription_plans (id) ON DELETE RESTRICT
)


    ALTER TABLE IF EXISTS user_subscriptions OWNER TO postgres;
    CREATE TABLE IF NOT EXISTS  academic_resources (
	id UUID NOT NULL, 
	title VARCHAR(255) NOT NULL, 
	description TEXT, 
	slug VARCHAR(255) NOT NULL, 
	grade_id UUID NOT NULL, 
	subject_id UUID NOT NULL, 
	topic_id UUID, 
	term academicterm NOT NULL, 
	year INTEGER NOT NULL, 
	pdf_url VARCHAR(512) NOT NULL, 
	thumbnail_url VARCHAR(512), 
	type_variant resourcetypevariant NOT NULL, 
	is_premium BOOLEAN NOT NULL, 
	is_published BOOLEAN NOT NULL, 
	is_archived BOOLEAN NOT NULL, 
	scheduled_publish_at TIMESTAMP WITH TIME ZONE, 
	published_at TIMESTAMP WITH TIME ZONE, 
	views_count INTEGER NOT NULL, 
	downloads_count INTEGER NOT NULL, 
	created_by_id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(grade_id) REFERENCES cbc_grades (id) ON DELETE RESTRICT, 
	FOREIGN KEY(subject_id) REFERENCES cbc_subjects (id) ON DELETE RESTRICT, 
	FOREIGN KEY(topic_id) REFERENCES cbc_topics (id) ON DELETE SET NULL, 
	FOREIGN KEY(created_by_id) REFERENCES users (id) ON DELETE RESTRICT
)


    ALTER TABLE IF EXISTS academic_resources OWNER TO postgres;
    CREATE TABLE IF NOT EXISTS  cbc_learning_outcomes (
	id UUID NOT NULL, 
	topic_id UUID NOT NULL, 
	statement TEXT NOT NULL, 
	code VARCHAR(50), 
	PRIMARY KEY (id), 
	FOREIGN KEY(topic_id) REFERENCES cbc_topics (id) ON DELETE CASCADE
)


    ALTER TABLE IF EXISTS cbc_learning_outcomes OWNER TO postgres;
    CREATE TABLE IF NOT EXISTS  cbc_resources (
	id UUID NOT NULL, 
	topic_id UUID NOT NULL, 
	title VARCHAR(150) NOT NULL, 
	resource_type resourcetype NOT NULL, 
	url VARCHAR(512) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(topic_id) REFERENCES cbc_topics (id) ON DELETE CASCADE
)


    ALTER TABLE IF EXISTS cbc_resources OWNER TO postgres;
    CREATE TABLE IF NOT EXISTS  class_assignments (
	id UUID NOT NULL, 
	classroom_id UUID NOT NULL, 
	subject_id UUID NOT NULL, 
	teacher_id UUID NOT NULL, 
	title VARCHAR(255) NOT NULL, 
	instructions TEXT NOT NULL, 
	due_date TIMESTAMP WITH TIME ZONE NOT NULL, 
	max_score INTEGER NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(classroom_id) REFERENCES classrooms (id) ON DELETE CASCADE, 
	FOREIGN KEY(subject_id) REFERENCES cbc_subjects (id) ON DELETE RESTRICT, 
	FOREIGN KEY(teacher_id) REFERENCES users (id) ON DELETE RESTRICT
)


    ALTER TABLE IF EXISTS class_assignments OWNER TO postgres;
    CREATE TABLE IF NOT EXISTS  classroom_enrollments (
	id UUID NOT NULL, 
	classroom_id UUID NOT NULL, 
	student_id UUID NOT NULL, 
	enrolled_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(classroom_id) REFERENCES classrooms (id) ON DELETE CASCADE, 
	FOREIGN KEY(student_id) REFERENCES users (id) ON DELETE CASCADE
)


    ALTER TABLE IF EXISTS classroom_enrollments OWNER TO postgres;
    CREATE TABLE IF NOT EXISTS  assignment_submissions (
	id UUID NOT NULL, 
	assignment_id UUID NOT NULL, 
	student_id UUID NOT NULL, 
	submission_text TEXT, 
	attachment_file_url VARCHAR(512), 
	status assignmentstatus NOT NULL, 
	score_achieved FLOAT, 
	teacher_feedback TEXT, 
	submitted_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	graded_at TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(assignment_id) REFERENCES class_assignments (id) ON DELETE CASCADE, 
	FOREIGN KEY(student_id) REFERENCES users (id) ON DELETE CASCADE
)


    ALTER TABLE IF EXISTS assignment_submissions OWNER TO postgres;
    CREATE TABLE IF NOT EXISTS  download_logs (
	id UUID NOT NULL, 
	resource_id UUID NOT NULL, 
	user_id UUID, 
	ip_address VARCHAR(45) NOT NULL, 
	device_fingerprint VARCHAR(512) NOT NULL, 
	country_code VARCHAR(3) NOT NULL, 
	downloaded_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(resource_id) REFERENCES academic_resources (id) ON DELETE CASCADE, 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE SET NULL
)


    ALTER TABLE IF EXISTS download_logs OWNER TO postgres;
    CREATE TABLE IF NOT EXISTS  resource_reviews (
	id UUID NOT NULL, 
	resource_id UUID NOT NULL, 
	user_id UUID NOT NULL, 
	rating INTEGER NOT NULL, 
	comment TEXT, 
	moderation_status reviewmoderationstatus NOT NULL, 
	is_reported BOOLEAN NOT NULL, 
	report_reason VARCHAR(255), 
	moderated_by_id UUID, 
	moderated_at TIMESTAMP WITH TIME ZONE, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(resource_id) REFERENCES academic_resources (id) ON DELETE CASCADE, 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
	FOREIGN KEY(moderated_by_id) REFERENCES users (id) ON DELETE SET NULL
)


    ALTER TABLE IF EXISTS resource_reviews OWNER TO postgres;
    CREATE TABLE IF NOT EXISTS  resource_tag_associations (
	resource_id UUID NOT NULL, 
	tag_id UUID NOT NULL, 
	PRIMARY KEY (resource_id, tag_id), 
	FOREIGN KEY(resource_id) REFERENCES academic_resources (id) ON DELETE CASCADE, 
	FOREIGN KEY(tag_id) REFERENCES content_tags (id) ON DELETE CASCADE
)


    ALTER TABLE IF EXISTS resource_tag_associations OWNER TO postgres;
    """))


def downgrade() -> None:
    op.execute(text("""
    DROP TABLE IF EXISTS resource_tag_associations CASCADE;
    DROP TABLE IF EXISTS resource_reviews CASCADE;
    DROP TABLE IF EXISTS download_logs CASCADE;
    DROP TABLE IF EXISTS assignment_submissions CASCADE;
    DROP TABLE IF EXISTS classroom_enrollments CASCADE;
    DROP TABLE IF EXISTS class_assignments CASCADE;
    DROP TABLE IF EXISTS cbc_resources CASCADE;
    DROP TABLE IF EXISTS cbc_learning_outcomes CASCADE;
    DROP TABLE IF EXISTS academic_resources CASCADE;
    DROP TABLE IF EXISTS user_subscriptions CASCADE;
    DROP TABLE IF EXISTS user_sessions CASCADE;
    DROP TABLE IF EXISTS profiles CASCADE;
    DROP TABLE IF EXISTS premium_subscriptions CASCADE;
    DROP TABLE IF EXISTS payment_transactions CASCADE;
    DROP TABLE IF EXISTS notification_preferences CASCADE;
    DROP TABLE IF EXISTS notification_logs CASCADE;
    DROP TABLE IF EXISTS classrooms CASCADE;
    DROP TABLE IF EXISTS cbc_topics CASCADE;
    DROP TABLE IF EXISTS users CASCADE;
    DROP TABLE IF EXISTS role_permissions CASCADE;
    DROP TABLE IF EXISTS cbc_subjects CASCADE;
    DROP TABLE IF EXISTS subscription_plans CASCADE;
    DROP TABLE IF EXISTS schools CASCADE;
    DROP TABLE IF EXISTS roles CASCADE;
    DROP TABLE IF EXISTS permissions CASCADE;
    DROP TABLE IF EXISTS content_tags CASCADE;
    DROP TABLE IF EXISTS cbc_grades CASCADE;
    """))
