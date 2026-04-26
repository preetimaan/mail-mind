from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import EmailAccount, Provider
from app.db.session import get_db


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


@router.get("/emails/accounts", response_model=list[AccountResponse])
def list_accounts(username: str, db: Session = Depends(get_db)) -> list[AccountResponse]:
    rows = db.execute(select(EmailAccount).where(EmailAccount.username == username).order_by(EmailAccount.id.asc()))
    accounts = list(rows.scalars().all())
    return [
        AccountResponse(
            id=a.id,
            username=a.username,
            provider=a.provider,
            email=a.email,
            is_active=a.is_active,
        )
        for a in accounts
    ]


@router.post("/emails/accounts", response_model=AccountResponse)
def create_account(req: AccountCreateRequest, db: Session = Depends(get_db)) -> AccountResponse:
    account = EmailAccount(username=req.username, provider=req.provider, email=str(req.email), is_active=True)
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
    )


@router.delete("/emails/accounts/{account_id}")
def delete_account(account_id: int, db: Session = Depends(get_db)) -> dict:
    account = db.get(EmailAccount, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    db.delete(account)
    db.commit()
    return {"message": "Account deleted"}

