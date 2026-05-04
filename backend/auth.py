import hashlib
import os
import uuid
from datetime import UTC, datetime, timedelta
from typing import Literal

import jwt
from fastapi import Depends, HTTPException, Request
from pydantic import BaseModel

JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-in-production")
JWT_EXPIRY_MINUTES = int(os.getenv("JWT_EXPIRY_MINUTES", "60"))
JWT_ALGORITHM = "HS256"


class User(BaseModel):
    username: str
    role: Literal["admin", "viewer"]


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


USERS = {
    "admin": {"password_hash": _hash_password("admin"), "role": "admin"},
    "viewer": {"password_hash": _hash_password("viewer"), "role": "viewer"},
}

API_KEYS = {
    "service-key-healthcare-rag": {"role": "admin", "service_name": "evaluation-runner"},
}


def authenticate_user(username: str, password: str) -> User | None:
    user_data = USERS.get(username)
    if not user_data:
        return None
    if user_data["password_hash"] != _hash_password(password):
        return None
    return User(username=username, role=user_data["role"])  # type: ignore[arg-type]


def create_token(username: str, role: str) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": username,
        "role": role,
        "iat": now,
        "exp": now + timedelta(minutes=JWT_EXPIRY_MINUTES),
        "jti": uuid.uuid4().hex,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.InvalidTokenError:
        return None


def _user_from_api_key(key: str) -> User | None:
    entry = API_KEYS.get(key)
    if not entry:
        return None
    return User(username=f"service:{entry['service_name']}", role=entry["role"])  # type: ignore[arg-type]


def get_current_user(request: Request) -> User:
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        payload = verify_token(token)
        if payload:
            return User(username=payload["sub"], role=payload["role"])

    api_key = request.headers.get("X-API-Key", "")
    if api_key:
        user = _user_from_api_key(api_key)
        if user:
            return user

    raise HTTPException(status_code=401, detail="Not authenticated")


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user
