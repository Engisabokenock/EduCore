"""
Create or update a pre-approved staff account (Super Admin or Admin) from the server.

Public sign-up creates administrators as *pending* applications that the Super Admin
must approve. Use this script to bootstrap the platform owner and any administrator
you want active immediately:

    cd backend
    python -m scripts.create_staff_account --role super_admin --email owner@example.com --name "Platform Owner"
    python -m scripts.create_staff_account --role admin --email ops@example.com --name "Operations Admin"

The password is read from the EDUCORE_ACCOUNT_PASSWORD environment variable or prompted
for interactively. It is never accepted as a command-line argument, which would leak
into shell history and process listings.

Only one Super Admin is allowed unless ``--allow-additional-owner`` is passed.
"""
import argparse
import asyncio
import getpass
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.future import select  # noqa: E402

import app.models  # noqa: E402,F401
from app.core.database import AsyncSessionLocal, engine  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.models.activity import ActivityCategory  # noqa: E402
from app.models.base import AccountApprovalStatus, Profile, Role, User, UserRole  # noqa: E402
from app.services import activity_service  # noqa: E402
from app.services.user_service import get_role, normalize_email, revoke_all_sessions  # noqa: E402

STAFF_ROLES = {"super_admin": UserRole.SUPER_ADMIN, "admin": UserRole.ADMIN}
MIN_PASSWORD_LENGTH = 12


def read_password() -> str:
    password = os.environ.get("EDUCORE_ACCOUNT_PASSWORD") or os.environ.get("EDUCORE_ADMIN_PASSWORD")
    if not password:
        password = getpass.getpass(f"Password (min {MIN_PASSWORD_LENGTH} chars): ")
        if password != getpass.getpass("Repeat password: "):
            raise SystemExit("Passwords do not match.")
    if len(password) < MIN_PASSWORD_LENGTH:
        raise SystemExit(f"Password must be at least {MIN_PASSWORD_LENGTH} characters.")
    return password


async def upsert_staff(email: str, name: str, role: UserRole, password: str, allow_additional_owner: bool) -> str:
    email = normalize_email(email)
    async with AsyncSessionLocal() as db:
        role_entity = await get_role(db, role)

        if role == UserRole.SUPER_ADMIN and not allow_additional_owner:
            other_owner = (await db.execute(
                select(User.email).join(Role, Role.id == User.role_id).where(
                    Role.name == UserRole.SUPER_ADMIN.value, User.email != email, User.is_active.is_(True)
                )
            )).scalars().first()
            if other_owner:
                raise SystemExit(
                    f"A Super Admin already exists ({other_owner}). The platform has a single owner; "
                    "pass --allow-additional-owner to override."
                )

        now = datetime.now(timezone.utc)
        user = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
        if user is None:
            user = User(email=email, hashed_password=hash_password(password), role_id=role_entity.id)
            user.profile = Profile(full_name=name[:100], metadata_fields={})
            db.add(user)
            action = "Created"
        else:
            user.role_id = role_entity.id
            user.hashed_password = hash_password(password)
            if user.profile and name:
                user.profile.full_name = name[:100]
            await revoke_all_sessions(db, user.id)
            action = "Updated"

        user.is_active = True
        user.is_verified = True
        user.approval_status = AccountApprovalStatus.APPROVED
        user.reviewed_at = now
        user.review_note = "Provisioned from the server console"
        await db.flush()

        activity_service.record(
            db,
            action="admin.staff_provisioned",
            category=ActivityCategory.ADMIN,
            summary=f"{action} {role.value} account {email} from the server console",
            actor_email="server-console",
            target_type="user",
            target_id=user.id,
            details={"role": role.value},
        )
        await db.commit()
    await engine.dispose()
    return f"{action} {role.value}: {email}"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--role", choices=sorted(STAFF_ROLES), required=True)
    parser.add_argument("--email", required=True)
    parser.add_argument("--name", default="")
    parser.add_argument("--allow-additional-owner", action="store_true")
    args = parser.parse_args()

    role = STAFF_ROLES[args.role]
    name = args.name or ("Platform Owner" if role == UserRole.SUPER_ADMIN else "Administrator")
    print(asyncio.run(upsert_staff(args.email, name, role, read_password(), args.allow_additional_owner)))


if __name__ == "__main__":
    main()
