"""
Student Mart - Administrator Provisioning Script
Safely creates or promotes an administrator user without hardcoding credentials.

Usage:
    python create_admin.py
    or
    python create_admin.py --email admin@college.ac.in --name "Campus Dean" --password "SecurePass123"
"""

import sys
import argparse
import getpass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import create_app
from app.models import db, User, College

def create_or_promote_admin(email, display_name=None, password=None, college_id=None):
    app = create_app()
    with app.app_context():
        user = User.query.filter_by(email=email.strip().lower()).first()

        if user:
            user.is_admin = True
            if password:
                user.set_password(password)
            if display_name:
                user.display_name = display_name
            db.session.commit()
            print(f"[SUCCESS] Existing user '{user.email}' ({user.display_name}) promoted to Administrator.")
            return True

        if not password:
            print("[ERROR] Password is required to create a new administrator account.")
            return False

        if not display_name:
            display_name = email.split("@")[0].title()

        new_admin = User(
            email=email.strip().lower(),
            display_name=display_name,
            college_id=college_id,
            course_year="Platform Administration",
            is_verified_student=True,
            is_admin=True,
            is_active=True
        )
        new_admin.set_password(password)
        db.session.add(new_admin)
        db.session.commit()
        print(f"[SUCCESS] Created new Administrator account for '{new_admin.email}' (ID: #{new_admin.id}).")
        return True

def main():
    parser = argparse.ArgumentParser(description="Student Mart - Administrator Provisioning Utility")
    parser.add_argument("--email", help="Administrator email address")
    parser.add_argument("--name", help="Display name for administrator")
    parser.add_argument("--password", help="Account password (omit for hidden terminal prompt)")
    args = parser.parse_args()

    email = args.email
    if not email:
        email = input("Enter administrator email: ").strip()

    if not email:
        print("[ERROR] Email cannot be empty.")
        sys.exit(1)

    display_name = args.name
    if not display_name and not User.query.filter_by(email=email).first():
        display_name = input("Enter administrator display name [Platform Admin]: ").strip() or "Platform Admin"

    password = args.password
    if not password:
        password = getpass.getpass("Enter administrator password: ")
        confirm = getpass.getpass("Confirm password: ")
        if password != confirm:
            print("[ERROR] Passwords do not match.")
            sys.exit(1)

    create_or_promote_admin(email, display_name, password)

if __name__ == "__main__":
    main()
