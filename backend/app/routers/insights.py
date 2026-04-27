from __future__ import annotations

from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import EmailAccount, EmailMessage, ProcessedRange
from app.db.session import get_db


router = APIRouter(tags=["insights"])


@router.get("/insights/summary")
def summary(username: str, account_id: int | None = None, db: Session = Depends(get_db)) -> dict:
    total_accounts = db.execute(
        select(func.count()).select_from(EmailAccount).where(EmailAccount.username == username)
    ).scalar_one()

    total_emails = db.execute(
        select(func.count())
        .select_from(EmailMessage)
        .join(EmailAccount, EmailAccount.id == EmailMessage.account_id)
        .where(EmailAccount.username == username)
    ).scalar_one()

    total_senders = db.execute(
        select(func.count(func.distinct(EmailMessage.sender_email)))
        .select_from(EmailMessage)
        .join(EmailAccount, EmailAccount.id == EmailMessage.account_id)
        .where(EmailAccount.username == username)
    ).scalar_one()

    processed_ranges = 0
    account_emails = 0
    account_senders = 0
    if account_id is not None:
        processed_ranges = db.execute(
            select(func.count()).select_from(ProcessedRange).where(ProcessedRange.account_id == account_id)
        ).scalar_one()
        account_emails = db.execute(
            select(func.count()).select_from(EmailMessage).where(EmailMessage.account_id == account_id)
        ).scalar_one()
        account_senders = db.execute(
            select(func.count(func.distinct(EmailMessage.sender_email)))
            .select_from(EmailMessage)
            .where(EmailMessage.account_id == account_id)
        ).scalar_one()

    return {
        "all_accounts": {"total_accounts": total_accounts, "total_emails": total_emails, "total_senders": total_senders},
        "current_account": {
            "account_emails": account_emails,
            "account_senders": account_senders,
            "processed_ranges": processed_ranges,
        },
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


@router.get("/insights/senders")
def top_senders(account_id: int, limit: int = 10, db: Session = Depends(get_db)) -> dict:
    rows = db.execute(
        select(EmailMessage.sender_email, func.count().label("count"))
        .where(EmailMessage.account_id == account_id)
        .group_by(EmailMessage.sender_email)
        .order_by(func.count().desc(), EmailMessage.sender_email.asc())
        .limit(limit)
    ).all()

    total_emails = db.execute(
        select(func.count()).select_from(EmailMessage).where(EmailMessage.account_id == account_id)
    ).scalar_one()

    domains_rows = db.execute(
        select(
            func.substr(EmailMessage.sender_email, func.instr(EmailMessage.sender_email, "@") + 1).label("domain"),
            func.count().label("count"),
        )
        .where(EmailMessage.account_id == account_id)
        .group_by("domain")
        .order_by(func.count().desc(), "domain")
        .limit(10)
    ).all()

    return {
        "total_emails": total_emails,
        "top_senders": [{"email": r.sender_email, "name": None, "count": int(r.count)} for r in rows],
        "top_domains": [{"domain": r.domain, "count": int(r.count)} for r in domains_rows],
    }


@router.get("/insights/categories")
def categories(account_id: int, db: Session = Depends(get_db)) -> dict:
    total = db.execute(select(func.count()).select_from(EmailMessage).where(EmailMessage.account_id == account_id)).scalar_one()
    rows = db.execute(
        select(EmailMessage.category, func.count().label("count"))
        .where(EmailMessage.account_id == account_id)
        .group_by(EmailMessage.category)
        .order_by(func.count().desc(), EmailMessage.category.asc())
    ).all()

    cats = []
    for r in rows:
        count = int(r.count)
        cats.append(
            {
                "category": r.category,
                "count": count,
                "percentage": (count / total * 100.0) if total else 0.0,
            }
        )

    return {"total": total, "categories": cats}


@router.get("/insights/frequency/yearly")
def yearly_frequency(account_id: int, db: Session = Depends(get_db)) -> dict:
    # SQLite: strftime('%Y', received_at)
    year_rows = db.execute(
        select(func.strftime("%Y", EmailMessage.received_at).label("year"), func.count().label("count"))
        .where(EmailMessage.account_id == account_id)
        .group_by("year")
        .order_by("year")
    ).all()

    yoy = []
    prev_total: int | None = None
    for r in year_rows:
        year = int(r.year)
        total = int(r.count)
        daily_avg = total / 365.0
        change = None if prev_total is None else (total - prev_total)
        change_pct = None if prev_total is None or prev_total == 0 else round((total - prev_total) / prev_total * 100)
        yoy.append(
            {
                "year": year,
                "total_emails": total,
                "daily_average": daily_avg,
                "change_from_previous": change,
                "change_percent": change_pct,
            }
        )
        prev_total = total

    return {"years": [y["year"] for y in yoy], "year_over_year": yoy}
