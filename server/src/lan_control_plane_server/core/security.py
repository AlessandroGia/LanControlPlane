from datetime import UTC, datetime, timedelta
from hmac import compare_digest
import hashlib
import secrets

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from lan_control_plane_server.core.config import get_settings

_password_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return _password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _password_hasher.verify(password_hash, password)
    except VerifyMismatchError:
        return False


def generate_session_token() -> str:
    return secrets.token_urlsafe(32)


def hash_session_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def get_session_expiry() -> datetime:
    settings = get_settings()
    return datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)


def validate_client_token(token: str) -> bool:
    settings = get_settings()
    return compare_digest(token, settings.client_token)


def validate_agent_token(token: str) -> bool:
    settings = get_settings()
    return compare_digest(token, settings.agent_token)
