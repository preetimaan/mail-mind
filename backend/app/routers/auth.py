import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth import create_access_token, get_current_username, jwt_secret
from app.database import User, get_db

router = APIRouter()


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1)
    login_secret: Optional[str] = None


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str


class MeResponse(BaseModel):
    username: str


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    """Obtain a JWT. If AUTH_LOGIN_SECRET is set in the environment, client must send matching login_secret."""
    expected = (os.getenv("AUTH_LOGIN_SECRET") or "").strip()
    if expected and (body.login_secret or "").strip() != expected:
        raise HTTPException(status_code=401, detail="Invalid login secret")

    jwt_secret()
    name = body.username.strip()
    user = db.query(User).filter(User.username == name).first()
    if not user:
        user = User(username=name)
        db.add(user)
        db.commit()
        db.refresh(user)

    token = create_access_token(name)
    return LoginResponse(access_token=token, username=name)


@router.get("/me", response_model=MeResponse)
def me(username: str = Depends(get_current_username)):
    return MeResponse(username=username)
