"""
Create or promote the platform owner (Super Admin) account.

Public sign-up can only create student/teacher/parent accounts, so the first Super
Admin must be bootstrapped from the server:

    cd backend
    python -m scripts.create_superadmin --email owner@educore.co.ke --name "Platform Owner"

The password is read from the EDUCORE_ADMIN_PASSWORD environment variable or prompted
for interactively (it is never accepted as a command-line argument, which would leak
into shell history and process listings).
"""
import argparse
import asyncio
import getpass
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.future import select  # noqa: E402

import app.models  # noqa: E402,F401
from app.core.database import AsyncSessionLocal, engine  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.models.base import Profile, User, UserRole  # noqa: E402
from app.services.user_service import get_role, normalize_email  # noqa: E402


async def main(email: str, name: str) -> None:
    password = os.environ.get("EDUCORE_ADMIN_PASSWORD") or getpass.getpass("Password (min 12 chars): ")
    if len(password) < 12:
        raise SystemExit("Password must be at least 12 characters.")

    async with AsyncSessionLocal() as db:
        role = await get_role(db, UserRole.SUPER_ADMIN)
        user = (await db.execute(select(User).where(User.email == normalize_email(email)))).scalar_one_or_none()
        if user is None:
            user = User(email=normalize_email(email), hashed_password=hash_password(password),
                        role_id=role.id, is_verified=True, is_active=True)
            user.profile = Profile(full_name=name, metadata_fields={})
            db.add(user)
            action = "Created"
        else:
            user.role_id = role.id
            user.hashed_password = hash_password(password)
            user.is_active = True
            user.is_verified = True
            action = "Promoted"
        await db.commit()
        print(f"{action} Super Admin: {user.email}")
    await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--email", required=True)
    parser.add_argument("--name", default="Platform Owner")
    args = parser.parse_args()
    asyncio.run(main(args.email, args.name))
