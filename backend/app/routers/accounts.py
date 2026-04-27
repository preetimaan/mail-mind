from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

import httpx

from app.db.models import AnalysisRun, EmailAccount, EmailMessage, OAuthCredential, OAuthProvider, OAuthState, ProcessedRange, Provider
from app.db.session import get_db
from app.services.credential_store import get_gmail_tokens
from app.settings import get_settings


router = APIRouter(tags=["accounts"])


class AccountCreateRequest(BaseModel):
    username: str = Field(..., min_length=1)
    provider: Provider
    email: EmailStr


class AccountResponse(BaseModel):
    id: int
    username: str
    provider: Provider
    email: EmailStr
    is_active: bool
    is_connected: bool


@router.get("/emails/accounts", response_model=list[AccountResponse])
def list_accounts(username: str, db: Session = Depends(get_db)) -> list[AccountResponse]:
    rows = db.execute(select(EmailAccount).where(EmailAccount.username == username).order_by(EmailAccount.id.asc()))
    accounts = list(rows.scalars().all())
    account_ids = [a.id for a in accounts]
    connected_ids: set[int] = set()
    if account_ids:
        connected = (
            db.execute(
                select(OAuthCredential.account_id).where(
                    OAuthCredential.account_id.in_(account_ids),
                    OAuthCredential.provider.in_([OAuthProvider.gmail, OAuthProvider.yahoo]),
                )
            )
            .scalars()
            .all()
        )
        connected_ids = set(connected)
    return [
        AccountResponse(
            id=a.id,
            username=a.username,
            provider=a.provider,
            email=a.email,
            is_active=a.is_active,
            is_connected=a.id in connected_ids,
        )
        for a in accounts
    ]


@router.post("/emails/accounts", response_model=AccountResponse)
def create_account(req: AccountCreateRequest, db: Session = Depends(get_db)) -> AccountResponse:
    # Provider-aware activation:
    # - Gmail requires OAuth connect flow
    # - Yahoo will require app-password auth flow
    # So accounts start inactive until authenticated.
    account = EmailAccount(username=req.username, provider=req.provider, email=str(req.email), is_active=False)
    db.add(account)
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to create account: {e}")
    db.refresh(account)
    return AccountResponse(
        id=account.id,
        username=account.username,
        provider=account.provider,
        email=account.email,
        is_active=account.is_active,
        is_connected=False,
    )


@router.delete("/emails/accounts/{account_id}")
def delete_account(account_id: int, db: Session = Depends(get_db)) -> dict:
    account = db.get(EmailAccount, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    # Cleanup: credentials + analysis artifacts.
    db.execute(delete(OAuthState).where(OAuthState.account_id == account.id))
    db.execute(delete(OAuthCredential).where(OAuthCredential.account_id == account.id))
    db.execute(delete(EmailMessage).where(EmailMessage.account_id == account.id))
    db.execute(delete(ProcessedRange).where(ProcessedRange.account_id == account.id))
    db.execute(delete(AnalysisRun).where(AnalysisRun.account_id == account.id))
    db.delete(account)
    db.commit()
    return {"message": "Account deleted"}


@router.post("/emails/accounts/{account_id}/deactivate", response_model=AccountResponse)
def deactivate_account(account_id: int, db: Session = Depends(get_db)) -> AccountResponse:
    """
    Dev/testing endpoint for reconnect UX.
    In the real provider integration, auth failures will mark accounts inactive.
    """
    account = db.get(EmailAccount, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    account.is_active = False
    db.commit()
    db.refresh(account)
    return AccountResponse(
        id=account.id,
        username=account.username,
        provider=account.provider,
        email=account.email,
        is_active=account.is_active,
        is_connected=False,
    )


@router.post("/emails/accounts/{account_id}/disconnect")
def disconnect_account(account_id: int, db: Session = Depends(get_db)) -> dict:
    account = db.get(EmailAccount, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    provider = OAuthProvider.gmail if account.provider == Provider.gmail else OAuthProvider.yahoo
    db.execute(
        delete(OAuthState).where(
            OAuthState.account_id == account.id,
            OAuthState.provider == provider,
        )
    )
    db.execute(
        delete(OAuthCredential).where(
            OAuthCredential.account_id == account.id,
            OAuthCredential.provider == provider,
        )
    )
    account.is_active = False
    db.commit()
    return {"message": "Account disconnected"}


@router.post("/emails/accounts/{account_id}/disconnect-gmail")
def disconnect_gmail_account(account_id: int, db: Session = Depends(get_db)) -> dict:
    """
    Gmail-specific disconnect:
    - best-effort revoke against Google
    - always delete local stored credentials
    """
    settings = get_settings()
    account = db.get(EmailAccount, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    if account.provider != Provider.gmail:
        raise HTTPException(status_code=409, detail="Account is not a Gmail provider")

    revoke_ok = False
    revoke_error: str | None = None

    tokens = get_gmail_tokens(db, settings, account.id)
    if tokens:
        token = tokens.refresh_token or tokens.access_token
        try:
            with httpx.Client(timeout=15.0) as client:
                res = client.post("https://oauth2.googleapis.com/revoke", data={"token": token})
            revoke_ok = res.status_code < 400
            if not revoke_ok:
                revoke_error = res.text
        except Exception as e:  # noqa: BLE001
            revoke_error = str(e)

    provider = OAuthProvider.gmail
    db.execute(delete(OAuthState).where(OAuthState.account_id == account.id, OAuthState.provider == provider))
    db.execute(delete(OAuthCredential).where(OAuthCredential.account_id == account.id, OAuthCredential.provider == provider))
    account.is_active = False
    db.commit()

    if tokens and not revoke_ok:
        return {"message": "Disconnected locally (revoke failed)", "revoke_error": revoke_error}
    return {"message": "Disconnected"}


@router.post("/emails/accounts/{account_id}/reset-data")
def reset_account_data(account_id: int, db: Session = Depends(get_db)) -> dict:
    account = db.get(EmailAccount, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    # Purge local analysis artifacts but keep credentials/account.
    db.execute(delete(EmailMessage).where(EmailMessage.account_id == account.id))
    db.execute(delete(ProcessedRange).where(ProcessedRange.account_id == account.id))
    db.execute(delete(AnalysisRun).where(AnalysisRun.account_id == account.id))
    db.commit()
    return {"message": "Local analysis data cleared"}

