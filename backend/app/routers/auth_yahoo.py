from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import EmailAccount, OAuthCredential, OAuthProvider, Provider
from app.db.session import get_db
from app.services.token_crypto import TokenCryptoError, encrypt_token
from app.settings import get_settings


router = APIRouter(tags=["auth"])


class YahooAppPasswordConnectRequest(BaseModel):
    account_id: int
    app_password: str = Field(..., min_length=6)


@router.post("/auth/yahoo/app-password")
def connect_yahoo_app_password(req: YahooAppPasswordConnectRequest, db: Session = Depends(get_db)) -> dict:
    settings = get_settings()

    account = db.get(EmailAccount, req.account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    if account.provider != Provider.yahoo:
        raise HTTPException(status_code=409, detail="Account is not a Yahoo provider")

    # NOTE: We intentionally don't validate against Yahoo yet (no IMAP/SMTP integration in rebuild MVP).
    # This endpoint only stores the secret securely so later provider work can use it.
    pw = req.app_password.strip()
    if len(pw) < 8:
        raise HTTPException(status_code=400, detail="App password looks too short")

    try:
        token_enc = encrypt_token(settings, pw)
    except TokenCryptoError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e

    cred = (
        db.execute(
            select(OAuthCredential).where(
                OAuthCredential.provider == OAuthProvider.yahoo,
                OAuthCredential.account_id == account.id,
            )
        )
        .scalars()
        .first()
    )
    if cred is None:
        cred = OAuthCredential(
            provider=OAuthProvider.yahoo,
            account_id=account.id,
            access_token_enc=token_enc,
            refresh_token_enc=None,
            expires_at=None,
            scope=None,
            token_type="app_password",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(cred)
    else:
        cred.access_token_enc = token_enc
        cred.token_type = "app_password"

    account.is_active = True
    db.commit()

    return {"message": "Yahoo app password stored"}

