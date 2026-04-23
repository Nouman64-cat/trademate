"""
make_admin.py - Promote a user to admin

Usage:
    python -m scripts.make_admin <email>
    python -m scripts.make_admin john@example.com
"""

import sys
import os
from pathlib import Path

# Add parent directory to path so we can import server modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlmodel import Session, select
from database.database import engine
from models.user import User


def make_admin(email: str) -> None:
    """Promote a user to admin by email address."""
    email = email.lower().strip()

    with Session(engine) as session:
        # Find user by email
        user = session.exec(select(User).where(User.email_address == email)).first()

        if not user:
            print(f"❌ Error: User with email '{email}' not found.")
            print("\nAvailable users:")
            all_users = session.exec(select(User)).all()
            for u in all_users:
                admin_badge = "👑 ADMIN" if u.is_admin else ""
                print(f"  - {u.email_address} ({u.user_name}) {admin_badge}")
            sys.exit(1)

        # Check if already admin
        if user.is_admin:
            print(f"✓ User '{user.user_name}' ({email}) is already an admin.")
            sys.exit(0)

        # Promote to admin
        user.is_admin = True
        session.add(user)
        session.commit()

        print(f"✓ Successfully promoted '{user.user_name}' ({email}) to admin!")
        print(f"\nUser Details:")
        print(f"  ID: {user.id}")
        print(f"  Name: {user.user_name}")
        print(f"  Email: {user.email_address}")
        print(f"  Is Admin: {user.is_admin}")
        print(f"  Is Verified: {user.is_verified}")
        print(f"  Status: {user.status}")


def list_admins() -> None:
    """List all admin users."""
    with Session(engine) as session:
        admins = session.exec(select(User).where(User.is_admin == True)).all()

        if not admins:
            print("No admin users found.")
            return

        print(f"Admin Users ({len(admins)}):")
        for admin in admins:
            print(f"  👑 {admin.user_name} ({admin.email_address}) - ID: {admin.id}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m scripts.make_admin <email>")
        print("   or: python -m scripts.make_admin --list")
        print("\nExamples:")
        print("  python -m scripts.make_admin john@example.com")
        print("  python -m scripts.make_admin --list")
        sys.exit(1)

    if sys.argv[1] == "--list":
        list_admins()
    else:
        make_admin(sys.argv[1])
