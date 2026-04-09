"""JWT bearer auth: token subject is the Mail Mind ``User.username``."""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

security = HTTPBearer(auto_error=False)


def jwt_secret() -> str:
    secret = (os.getenv("JWT_SECRET") or "").strip()
    if not secret:
        raise HTTPException(
            status_code=503,
            detail="Server is not configured for authentication (set JWT_SECRET).",
        )
    return secret


def create_access_token(username: str) -> str:
    days = int(os.getenv("JWT_EXPIRE_DAYS", "7"))
    payload = {
        "sub": username,
        "exp": datetime.now(timezone.utc) + timedelta(days=days),
    }
    return jwt.encode(payload, jwt_secret(), algorithm="HS256")


def decode_access_token(token: str) -> str:
    try:
        data = jwt.decode(token, jwt_secret(), algorithms=["HS256"])
        sub = data.get("sub")
        if not sub or not isinstance(sub, str):
            raise ValueError("missing sub")
        return sub
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def get_current_username(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> str:
    if creds is None or (creds.scheme or "").lower() != "bearer":
        raise HTTPException(status_code=401, detail="Not authenticated")
    return decode_access_token(creds.credentials)
