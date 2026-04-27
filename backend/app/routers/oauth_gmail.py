from __future__ import annotations

import secrets
from datetime import datetime, timedelta
from urllib.parse import quote, urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.models import EmailAccount, OAuthCredential, OAuthProvider, OAuthState, Provider
from app.db.session import get_db
from app.services.token_crypto import TokenCryptoError, encrypt_token
from app.settings import get_settings


router = APIRouter(tags=["oauth"])


class GmailOAuthStartRequest(BaseModel):
    account_id: int


@router.post("/oauth/gmail/start")
def gmail_oauth_start(req: GmailOAuthStartRequest, db: Session = Depends(get_db)) -> dict:
    settings = get_settings()
    if not settings.gmail_client_id or not settings.gmail_client_secret:
        raise HTTPException(status_code=409, detail="Gmail OAuth is not configured (missing client id/secret)")

    account = db.get(EmailAccount, req.account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    if account.provider != Provider.gmail:
        raise HTTPException(status_code=409, detail="Account is not a Gmail provider")

    state = secrets.token_urlsafe(32)
    db.add(
        OAuthState(
            provider=OAuthProvider.gmail,
            state=state,
            account_id=account.id,
            expires_at=datetime.utcnow() + timedelta(minutes=10),
        )
    )
    db.commit()

    qs = urlencode(
        {
            "client_id": settings.gmail_client_id,
            "redirect_uri": settings.gmail_redirect_uri,
            "response_type": "code",
            "scope": "https://www.googleapis.com/auth/gmail.readonly",
            "access_type": "offline",
            "prompt": "consent",
            "include_granted_scopes": "true",
            "state": state,
        }
    )
    return {"auth_url": f"https://accounts.google.com/o/oauth2/v2/auth?{qs}"}


@router.get("/oauth/gmail/callback")
def gmail_oauth_callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    db: Session = Depends(get_db),
) -> RedirectResponse:
    settings = get_settings()

    if error:
        safe = quote(error, safe="")
        return RedirectResponse(
            url=f"{settings.frontend_url}/?tab=settings&oauth=gmail&status=error&message={safe}",
            status_code=302,
        )
    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing code/state")

    row = db.execute(select(OAuthState).where(OAuthState.state == state)).scalars().first()
    if not row:
        raise HTTPException(status_code=400, detail="Invalid state")
    if row.expires_at < datetime.utcnow():
        db.execute(delete(OAuthState).where(OAuthState.id == row.id))
        db.commit()
        raise HTTPException(status_code=400, detail="Expired state")

    if not settings.gmail_client_id or not settings.gmail_client_secret:
        raise HTTPException(status_code=409, detail="Gmail OAuth is not configured (missing client id/secret)")

    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "client_id": settings.gmail_client_id,
        "client_secret": settings.gmail_client_secret,
        "code": code,
        "redirect_uri": settings.gmail_redirect_uri,
        "grant_type": "authorization_code",
    }
    try:
        with httpx.Client(timeout=15.0) as client:
            res = client.post(token_url, data=data)
        if res.status_code >= 400:
            raise HTTPException(status_code=400, detail=f"Token exchange failed: {res.text}")
        payload = res.json()
    except HTTPException:
        raise
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"Token exchange failed: {e}") from e

    access_token = payload.get("access_token")
    refresh_token = payload.get("refresh_token")
    expires_in = payload.get("expires_in")
    scope = payload.get("scope")
    token_type = payload.get("token_type")
    if not access_token:
        raise HTTPException(status_code=400, detail="Token exchange did not return access_token")

    try:
        access_token_enc = encrypt_token(settings, access_token)
        refresh_token_enc = encrypt_token(settings, refresh_token) if refresh_token else None
    except TokenCryptoError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e

    expires_at = datetime.utcnow() + timedelta(seconds=int(expires_in)) if expires_in else None

    cred = (
        db.execute(
            select(OAuthCredential).where(
                OAuthCredential.provider == OAuthProvider.gmail,
                OAuthCredential.account_id == row.account_id,
            )
        )
        .scalars()
        .first()
    )
    if cred is None:
        cred = OAuthCredential(
            provider=OAuthProvider.gmail,
            account_id=row.account_id,
            access_token_enc=access_token_enc,
            refresh_token_enc=refresh_token_enc,
            expires_at=expires_at,
            scope=scope,
            token_type=token_type,
        )
        db.add(cred)
    else:
        cred.access_token_enc = access_token_enc
        if refresh_token_enc:
            cred.refresh_token_enc = refresh_token_enc
        cred.expires_at = expires_at
        cred.scope = scope
        cred.token_type = token_type

    account = db.get(EmailAccount, row.account_id)
    if account:
        account.is_active = True

    db.execute(delete(OAuthState).where(OAuthState.id == row.id))
    db.commit()

    return RedirectResponse(
        url=f"{settings.frontend_url}/?tab=settings&oauth=gmail&status=ok&account_id={row.account_id}",
        status_code=302,
    )

