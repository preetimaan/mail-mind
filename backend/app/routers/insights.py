from __future__ import annotations

from datetime import date, timedelta

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


def _merge_ranges(ranges: list[tuple[date, date]]) -> list[tuple[date, date]]:
    if not ranges:
        return []
    ranges = sorted(ranges, key=lambda r: (r[0], r[1]))
    merged: list[tuple[date, date]] = [ranges[0]]
    for start, end in ranges[1:]:
        last_start, last_end = merged[-1]
        if start <= last_end:
            merged[-1] = (last_start, max(last_end, end))
        else:
            merged.append((start, end))
    return merged


@router.get("/insights/processed-ranges/gaps")
def processed_range_gaps(
    account_id: int,
    start_date: date | None = None,
    end_date_exclusive: date | None = None,
    db: Session = Depends(get_db),
) -> list[dict]:
    """
    Returns missing (unprocessed) ranges within a window.

    Defaults to last 365 days through tomorrow (exclusive) if not provided.
    """
    today = date.today()
    window_start = start_date or (today - timedelta(days=365))
    window_end = end_date_exclusive or (today + timedelta(days=1))

    if window_end <= window_start:
        return []

    rows = db.execute(
        select(ProcessedRange.start_date, ProcessedRange.end_date_exclusive)
        .where(ProcessedRange.account_id == account_id)
        .where(ProcessedRange.end_date_exclusive > window_start)
        .where(ProcessedRange.start_date < window_end)
    ).all()

    covered = _merge_ranges(
        [
            (max(r.start_date, window_start), min(r.end_date_exclusive, window_end))
            for r in rows
            if r.end_date_exclusive > window_start and r.start_date < window_end
        ]
    )

    gaps: list[tuple[date, date]] = []
    cursor = window_start
    for start, end in covered:
        if cursor < start:
            gaps.append((cursor, start))
        cursor = max(cursor, end)
    if cursor < window_end:
        gaps.append((cursor, window_end))

    return [
        {
            "start_date": gs.isoformat(),
            "end_date_exclusive": ge.isoformat(),
            "days": (ge - gs).days,
        }
        for gs, ge in gaps
        if (ge - gs).days > 0
    ]
