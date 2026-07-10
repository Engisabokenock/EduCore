"""Generate an initial Alembic migration from current SQLAlchemy models."""
import os
import sys
from datetime import datetime, timezone
from sqlalchemy import text
from sqlalchemy.schema import CreateTable, DropTable

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import Base, engine
import app.models.base
import app.models.cbc
import app.models.resource
import app.models.subscription
import app.models.payment
import app.models.review
import app.models.analytics
import app.models.download
import app.models.grade
import app.models.notification
import app.models.school
import app.models.subject
import app.models.topic
import app.models.tracking


def get_dialect(dialect_name: str = "postgresql"):
    module_path = f"sqlalchemy.dialects.{dialect_name}"
    dialect_cls = __import__(module_path, fromlist=["dialect"]).dialect()
    return dialect_cls


def collect_enums():
    enum_classes = {}
    for table in Base.metadata.sorted_tables:
        for column in table.columns:
            coltype = getattr(column, "type", None)
            if type(coltype).__name__ == "Enum" and getattr(coltype, "enum_class", None) is not None:
                enum_classes[coltype.enum_class.__name__] = coltype.enum_class
    return enum_classes


def compile_ddl(dialect_name: str = "postgresql"):
    dialect_cls = get_dialect(dialect_name)
    stmts = []
    for enum_name, enum_cls in collect_enums().items():
        values = ", ".join(f"'{member.value}'" for member in enum_cls)
        stmts.append(f"DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = '{enum_name.lower()}') THEN CREATE TYPE {enum_name.lower()} AS ENUM ({values}); END IF; END $$;")
    for table in Base.metadata.sorted_tables:
        raw_ddl = str(CreateTable(table).compile(dialect=dialect_cls))
        stmts.append(f"CREATE TABLE IF NOT EXISTS {raw_ddl[len('CREATE TABLE '):]}")
        stmts.append(f"ALTER TABLE IF EXISTS {table.name} OWNER TO postgres;")
    return stmts


def write_migration():
    revision = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    upgrade_sql = "\n    ".join(compile_ddl())
    downgrade_sql = "\n    ".join(
        f"DROP TABLE IF EXISTS {table.name} CASCADE;" for table in reversed(Base.metadata.sorted_tables)
    )

    content = f'''"""Initial schema snapshot

Revision ID: {revision}
Revises:
Create Date: {datetime.now(timezone.utc).isoformat()}
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

revision: str = {repr(revision)}
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(text("""
    {upgrade_sql}
    """))


def downgrade() -> None:
    op.execute(text("""
    {downgrade_sql}
    """))
'''
    versions_dir = os.path.join(os.path.dirname(__file__), "..", "alembic", "versions")
    os.makedirs(versions_dir, exist_ok=True)
    path = os.path.join(versions_dir, f"{revision}_initial_schema.py")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    for old in [f for f in os.listdir(versions_dir) if f.endswith("_initial_schema.py") and f != os.path.basename(path)]:
        os.remove(os.path.join(versions_dir, old))
    print(f"Generated {path}")


if __name__ == "__main__":
    write_migration()
