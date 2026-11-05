"""
Create or promote the platform owner (Super Admin) account.

Kept for existing runbooks; it delegates to ``scripts.create_staff_account``:

    cd backend
    python -m scripts.create_superadmin --email owner@educore.co.ke --name "Platform Owner"

The password is read from EDUCORE_ACCOUNT_PASSWORD (or EDUCORE_ADMIN_PASSWORD) or
prompted for interactively.
"""
import argparse
import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.models.base import UserRole  # noqa: E402
from scripts.create_staff_account import read_password, upsert_staff  # noqa: E402

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--email", required=True)
    parser.add_argument("--name", default="Platform Owner")
    parser.add_argument("--allow-additional-owner", action="store_true")
    args = parser.parse_args()
    print(asyncio.run(upsert_staff(args.email, args.name, UserRole.SUPER_ADMIN, read_password(),
                                   args.allow_additional_owner)))
