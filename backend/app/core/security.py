import os
import magic
from datetime import datetime, timedelta, timezone
from typing import Any, Dict
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import UploadFile
from app.core.config import settings
from app.core.exceptions import AuthenticationError, AppBaseException

# High-entropy Argon2id hashing configuration.
# bcrypt is retained in the context (deprecated) so that existing bcrypt password
# hashes remain verifiable while new hashes are produced with Argon2id.
pwd_context = CryptContext(
    schemes=["argon2", "bcrypt"],
    deprecated="auto",
    argon2__time_cost=3,        # Computational iterations
    argon2__memory_cost=65536,  # RAM footprint in KB (64MB)
    argon2__parallelism=4,      # Execution threads
)

# Strictly constrained whitelist of allowed application signatures
ALLOWED_MIME_TYPES = ["application/pdf"]
MAX_FILE_SIZE_BYTES = 15 * 1024 * 1024  # 15 Megabytes Max Constraint

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_jwt_token(subject: Any, expires_delta: timedelta, is_refresh: bool = False) -> str:
    secret = settings.JWT_REFRESH_SECRET if is_refresh else settings.JWT_SECRET_KEY
    now = datetime.now(timezone.utc)
    payload = {
        "exp": now + expires_delta,
        "sub": str(subject),
        "type": "refresh" if is_refresh else "access",
        "iat": now,
        "nbf": now,
    }
    return jwt.encode(payload, secret, algorithm="HS256")

def verify_jwt_token(token: str, is_refresh: bool = False) -> Dict[str, Any]:
    secret = settings.JWT_REFRESH_SECRET if is_refresh else settings.JWT_SECRET_KEY
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        token_type = "refresh" if is_refresh else "access"
        if payload.get("type") != token_type:
            raise AuthenticationError("Malformed payload execution scope validation dropped")
        return payload
    except JWTError:
        raise AuthenticationError("Cryptographic token signature verification failed")

async def validate_uploaded_file(file: UploadFile) -> None:
    """
    Enforces strict structural file protection validations.

    Checks content sizes and inspects byte headers using magic numbers to block extension spoofing.
    """
    # 1. Volumetric Dimension Verification
    file.file.seek(0, os.SEEK_END)
    size = file.file.tell()
    file.file.seek(0)  # Reset stream tracker immediately

    if size > MAX_FILE_SIZE_BYTES:
        raise AppBaseException("Payload limit exceeded: Maximum allowable size bound is 15MB", 413)

    # 2. Magic Bytes Content-Type Deep Inspection
    header_bytes = await file.read(2048)
    await file.seek(0)  # Keep binary stream state clean for downstream storage blocks

    detected_mime = magic.from_buffer(header_bytes, mime=True)
    if detected_mime not in ALLOWED_MIME_TYPES:
        raise AppBaseException(f"Malicious file format rejected: Mimetic signature '{detected_mime}' is not permitted", 415)
