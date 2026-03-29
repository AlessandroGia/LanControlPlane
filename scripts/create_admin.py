from __future__ import annotations

import getpass
import os
import sys
from pathlib import Path

from lan_control_plane_server.core.security import hash_password
from lan_control_plane_server.db.session import SessionLocal
from lan_control_plane_server.services.auth_service import AuthService


def read_password() -> str:
    password_file = os.getenv("LCP_ADMIN_PASSWORD_FILE")
    password = os.getenv("LCP_ADMIN_PASSWORD")

    if password_file:
        content = Path(password_file).read_text(encoding="utf-8").strip()
        if not content:
            raise ValueError("Password file is empty")
        return content

    if password:
        return password.strip()

    entered = getpass.getpass("Admin password: ").strip()
    confirm = getpass.getpass("Confirm password: ").strip()

    if not entered:
        raise ValueError("Password cannot be empty")

    if entered != confirm:
        raise ValueError("Passwords do not match")

    return entered


def main() -> int:
    username = os.getenv("LCP_ADMIN_USERNAME", "admin")
    role = os.getenv("LCP_ADMIN_ROLE", "admin")
    update_if_exists = os.getenv("LCP_ADMIN_UPDATE_IF_EXISTS", "false").lower() == "true"

    try:
        password = read_password()
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    session = SessionLocal()
    try:
        auth_service = AuthService(session)
        existing = auth_service.user_repository.get_by_username(username)

        if existing is None:
            user = auth_service.create_user(
                username=username,
                password=password,
                role=role,
            )
            print(f"Created user: {user.username}")
            return 0

        if not update_if_exists:
            print(f"User already exists: {existing.username}")
            return 0

        auth_service.user_repository.update_password_and_role(
            existing,
            password_hash=hash_password(password),
            role=role,
        )
        print(f"Updated user: {existing.username}")
        return 0
    finally:
        session.close()


if __name__ == "__main__":
    raise SystemExit(main())
