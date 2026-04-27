from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import EmailAccount, ProcessedRange
from app.db.session import get_db


router = APIRouter(tags=["insights"])


@router.get("/insights/summary")
def summary(username: str, account_id: int | None = None, db: Session = Depends(get_db)) -> dict:
    total_accounts = db.execute(
        select(func.count()).select_from(EmailAccount).where(EmailAccount.username == username)
    ).scalar_one()

    # Stub until EmailMessage exists.
    total_emails = 0
    total_senders = 0

    processed_ranges = 0
    if account_id is not None:
        processed_ranges = db.execute(
            select(func.count()).select_from(ProcessedRange).where(ProcessedRange.account_id == account_id)
        ).scalar_one()

    return {
        "all_accounts": {"total_accounts": total_accounts, "total_emails": total_emails, "total_senders": total_senders},
        "current_account": {"account_emails": 0, "account_senders": 0, "processed_ranges": processed_ranges},
    }


@router.get("/insights/processed-ranges")
def processed_ranges(account_id: int, db: Session = Depends(get_db)) -> list[dict]:
    rows = db.execute(
        select(
            ProcessedRange.start_date,
            ProcessedRange.end_date_exclusive,
            ProcessedRange.emails_count,
            ProcessedRange.processed_at,
        )
        .where(ProcessedRange.account_id == account_id)
        .order_by(ProcessedRange.start_date.asc(), ProcessedRange.end_date_exclusive.asc())
    ).all()
    return [
        {
            "start_date": r.start_date.isoformat(),
            "end_date_exclusive": r.end_date_exclusive.isoformat(),
            "emails_count": int(r.emails_count),
            "processed_at": r.processed_at.isoformat(),
        }
        for r in rows
    ]
