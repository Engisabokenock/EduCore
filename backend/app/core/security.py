import hashlib
import hmac
import os
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from fastapi import UploadFile
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.core.exceptions import AppBaseException, AuthenticationError

# Argon2id for new hashes. bcrypt stays in the context (deprecated) so existing
# bcrypt hashes still verify and are transparently upgraded on next login.
pwd_context = CryptContext(
    schemes=["argon2", "bcrypt"],
    deprecated="auto",
    argon2__time_cost=3,
    argon2__memory_cost=65536,  # 64 MB
    argon2__parallelism=4,
)

JWT_ALGORITHM = "HS256"

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "text/csv",
    "application/msword",
    "application/vnd.ms-excel",
    "application/vnd.ms-powerpoint",
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
    "video/mp4",
    "video/quicktime",
    "application/zip",
    "application/x-zip-compressed",
}


# ── Passwords ────────────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except (ValueError, TypeError):
        # Malformed / unknown hash formats must fail closed, not 500.
        return False


def password_needs_rehash(hashed_password: str) -> bool:
    try:
        return pwd_context.needs_update(hashed_password)
    except (ValueError, TypeError):
        return False


# Constant-time dummy verification so "unknown e-mail" and "wrong password" take the
# same time and cannot be used to enumerate registered accounts.
_DUMMY_HASH = pwd_context.hash(secrets.token_urlsafe(16))


def burn_password_check(plain_password: str) -> None:
    verify_password(plain_password, _DUMMY_HASH)


# ── Opaque tokens (e-mail verification, password reset) ──────────────────────

def generate_token() -> str:
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """Digest stored in the database; the raw token only ever lives in the e-mail."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def constant_time_equals(a: str, b: str) -> bool:
    return hmac.compare_digest(a.encode("utf-8"), b.encode("utf-8"))


# ── JWT ──────────────────────────────────────────────────────────────────────

def create_jwt_token(subject: Any, expires_delta: timedelta, is_refresh: bool = False) -> str:
    secret = settings.JWT_REFRESH_SECRET if is_refresh else settings.JWT_SECRET_KEY
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(subject),
        "type": "refresh" if is_refresh else "access",
        "iat": now,
        "nbf": now,
        "exp": now + expires_delta,
        # Unique id: two tokens minted for the same user in the same second must differ,
        # otherwise the refresh-token uniqueness constraint rejects the second session.
        "jti": uuid.uuid4().hex,
    }
    return jwt.encode(payload, secret, algorithm=JWT_ALGORITHM)


def create_token_pair(subject: Any) -> Dict[str, str]:
    return {
        "access": create_jwt_token(subject, timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)),
        "refresh": create_jwt_token(subject, timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS), is_refresh=True),
    }


def verify_jwt_token(token: str, is_refresh: bool = False) -> Dict[str, Any]:
    secret = settings.JWT_REFRESH_SECRET if is_refresh else settings.JWT_SECRET_KEY
    expected_type = "refresh" if is_refresh else "access"
    try:
        payload = jwt.decode(token, secret, algorithms=[JWT_ALGORITHM])
    except JWTError:
        raise AuthenticationError("Your session has expired. Please log in again.")
    if payload.get("type") != expected_type or not payload.get("sub"):
        raise AuthenticationError("Invalid authentication token.")
    try:
        uuid.UUID(str(payload["sub"]))
    except ValueError:
        raise AuthenticationError("Invalid authentication token.")
    return payload


# ── Uploads ──────────────────────────────────────────────────────────────────

def _detect_mime(header_bytes: bytes) -> str:
    try:
        import magic  # python-magic needs the system libmagic; imported lazily so the API still boots without it
    except ImportError as exc:  # pragma: no cover - environment specific
        raise AppBaseException("File type inspection is unavailable on this server (libmagic missing).", 503) from exc
    return magic.from_buffer(header_bytes, mime=True)


async def validate_uploaded_file(file: UploadFile, allowed: set[str] | None = None) -> str:
    """
    Enforce size limits and inspect magic bytes so a renamed executable cannot be
    uploaded as a PDF. Returns the detected MIME type.
    """
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    file.file.seek(0, os.SEEK_END)
    size = file.file.tell()
    file.file.seek(0)

    if size == 0:
        raise AppBaseException("The uploaded file is empty.", 400)
    if size > max_bytes:
        raise AppBaseException(f"File too large. The maximum size is {settings.MAX_UPLOAD_SIZE_MB} MB.", 413)

    header_bytes = await file.read(2048)
    await file.seek(0)

    detected_mime = _detect_mime(header_bytes)
    if detected_mime not in (allowed or ALLOWED_MIME_TYPES):
        raise AppBaseException(f"File type '{detected_mime}' is not allowed.", 415)
    return detected_mime


def safe_filename(filename: str | None, default: str = "upload") -> str:
    """Strip paths and unsafe characters from a client-supplied filename."""
    name = os.path.basename(filename or default).strip() or default
    cleaned = "".join(ch if ch.isalnum() or ch in "._-" else "-" for ch in name)
    return cleaned[-120:].lstrip(".") or default
