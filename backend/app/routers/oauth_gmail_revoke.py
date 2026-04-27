from __future__ import annotations

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.models import EmailAccount, OAuthProvider, Provider
from app.db.session import get_db
from app.services.credential_store import get_gmail_tokens
from app.settings import get_settings


router = APIRouter(tags=["oauth"])


class GmailRevokeRequest(BaseModel):
    account_id: int


@router.post("/oauth/gmail/revoke")
def gmail_revoke(req: GmailRevokeRequest, db: Session = Depends(get_db)) -> dict:
    """
    Best-effort revoke against Google's token revocation endpoint.

    This does NOT delete local credentials; use /emails/accounts/{id}/disconnect for that.
    """
    settings = get_settings()
    account = db.get(EmailAccount, req.account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    if account.provider != Provider.gmail:
        raise HTTPException(status_code=409, detail="Account is not a Gmail provider")

    tokens = get_gmail_tokens(db, settings, account.id)
    if not tokens:
        return {"message": "No stored Gmail tokens to revoke"}

    # Prefer revoking refresh token when present; else revoke access token.
    token = tokens.refresh_token or tokens.access_token
    try:
        with httpx.Client(timeout=15.0) as client:
            res = client.post("https://oauth2.googleapis.com/revoke", data={"token": token})
        # Google returns 200 for success; treat other codes as failure but non-fatal.
        if res.status_code >= 400:
            raise HTTPException(status_code=400, detail=f"Revoke failed: {res.text}")
    except HTTPException:
        raise
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"Revoke failed: {e}") from e

    return {"message": "Gmail token revoked"}

