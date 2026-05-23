from __future__ import annotations

import hashlib

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader

from config import SALON_API_KEY


API_KEY_NAME = "api-key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    return hash_password(password) == password_hash


def get_api_key(api_key: str | None = Depends(api_key_header)) -> str:
    if api_key != SALON_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
    return api_key
