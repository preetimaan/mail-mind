from __future__ import annotations

import json
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.db.models import AnalysisRun, AnalysisStatus, EmailAccount, EmailMessage, ProcessedRange
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
        completed_runs = db.execute(
            select(func.count())
            .select_from(AnalysisRun)
            .where(AnalysisRun.account_id == account_id, AnalysisRun.status == AnalysisStatus.completed)
        ).scalar_one()
        legacy_rows = db.execute(
            select(
                ProcessedRange.start_date,
                ProcessedRange.end_date_exclusive,
                ProcessedRange.emails_count,
                ProcessedRange.processed_at,
            )
            .where(ProcessedRange.account_id == account_id)
            .where(ProcessedRange.analysis_run_id.is_(None))
        ).all()
        legacy_tuples_summary = [
            (row.start_date, row.end_date_exclusive, int(row.emails_count), row.processed_at) for row in legacy_rows
        ]
        legacy_display = len(_merge_legacy_processed_rows(legacy_tuples_summary))
        processed_ranges = int(completed_runs) + legacy_display
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


def _merge_legacy_processed_rows(rows: list[tuple[date, date, int, datetime]]) -> list[dict]:
    """Merge old per-chunk ProcessedRange rows (analysis_run_id NULL) into contiguous windows."""
    if not rows:
        return []
    sorted_rows = sorted(rows, key=lambda t: (t[0], t[1]))
    merged_starts: list[date] = []
    merged_ends: list[date] = []
    merged_counts: list[int] = []
    merged_times: list[datetime] = []
    for start, end, cnt, ts in sorted_rows:
        if merged_starts and start <= merged_ends[-1]:
            merged_ends[-1] = max(merged_ends[-1], end)
            merged_counts[-1] += cnt
            merged_times[-1] = max(merged_times[-1], ts)
        else:
            merged_starts.append(start)
            merged_ends.append(end)
            merged_counts.append(cnt)
            merged_times.append(ts)
    return [
        {
            "start_date": merged_starts[i].isoformat(),
            "end_date_exclusive": merged_ends[i].isoformat(),
            "emails_count": merged_counts[i],
            "processed_at": merged_times[i].isoformat(),
            "analysis_run_id": None,
        }
        for i in range(len(merged_starts))
    ]


@router.get("/insights/processed-ranges")
def processed_ranges(account_id: int, db: Session = Depends(get_db)) -> list[dict]:
    """
    User-facing coverage: one row per completed analysis (the date range the user requested),
    not one row per internal CHUNK_DAYS slice. Legacy rows without analysis_run_id are merged.
    """
    runs = db.execute(
        select(AnalysisRun)
        .where(AnalysisRun.account_id == account_id, AnalysisRun.status == AnalysisStatus.completed)
        .order_by(AnalysisRun.finished_at.desc(), AnalysisRun.id.desc())
    ).scalars().all()

    completed_payload = [
        {
            "start_date": r.start_date.isoformat(),
            "end_date_exclusive": r.end_date_exclusive.isoformat(),
            "emails_count": int(r.emails_processed),
            "processed_at": (r.finished_at or r.created_at).isoformat(),
            "analysis_run_id": r.id,
        }
        for r in runs
    ]

    legacy_rows = db.execute(
        select(
            ProcessedRange.start_date,
            ProcessedRange.end_date_exclusive,
            ProcessedRange.emails_count,
            ProcessedRange.processed_at,
        )
        .where(ProcessedRange.account_id == account_id)
        .where(ProcessedRange.analysis_run_id.is_(None))
        .order_by(ProcessedRange.start_date.asc(), ProcessedRange.end_date_exclusive.asc())
    ).all()
    legacy_tuples = [(row.start_date, row.end_date_exclusive, int(row.emails_count), row.processed_at) for row in legacy_rows]
    legacy_payload = _merge_legacy_processed_rows(legacy_tuples)

    return completed_payload + legacy_payload


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
def top_senders(account_id: int, limit: int = 10, include_automated: bool = False, db: Session = Depends(get_db)) -> dict:
    # Best-effort filter: by default, suppress obvious automated/system senders.
    # (Still available via include_automated=true.)
    automated_patterns = [
        "%noreply%",
        "%no-reply%",
        "%donotreply%",
        "%do-not-reply%",
        "%mailer-daemon%",
        "%postmaster%",
    ]
    base = [EmailMessage.account_id == account_id]
    if not include_automated:
        lower_sender = func.lower(EmailMessage.sender_email)
        for p in automated_patterns:
            base.append(lower_sender.not_like(p))
    rows = db.execute(
        select(EmailMessage.sender_email, func.count().label("count"))
        .where(*base)
        .group_by(EmailMessage.sender_email)
        .order_by(func.count().desc(), EmailMessage.sender_email.asc())
        .limit(limit)
    ).all()

    top_emails = [r.sender_email for r in rows]
    name_by_email: dict[str, str | None] = {e: None for e in top_emails}
    if top_emails:
        # Best-effort display name: most frequently observed sender_name for that sender_email.
        # (We intentionally avoid trying to "decode" Gmail display names beyond what providers give us.)
        name_counts = (
            select(
                EmailMessage.sender_email.label("sender_email"),
                EmailMessage.sender_name.label("sender_name"),
                func.count().label("name_count"),
            )
            .where(*base)
            .where(EmailMessage.sender_email.in_(top_emails))
            .where(EmailMessage.sender_name.is_not(None))
            .where(EmailMessage.sender_name != "")
            .group_by(EmailMessage.sender_email, EmailMessage.sender_name)
            .subquery()
        )

        max_counts = (
            select(
                name_counts.c.sender_email.label("sender_email"),
                func.max(name_counts.c.name_count).label("max_count"),
            )
            .group_by(name_counts.c.sender_email)
            .subquery()
        )

        best_names = db.execute(
            select(
                name_counts.c.sender_email,
                func.min(name_counts.c.sender_name).label("sender_name"),
            )
            .join(
                max_counts,
                and_(
                    name_counts.c.sender_email == max_counts.c.sender_email,
                    name_counts.c.name_count == max_counts.c.max_count,
                ),
            )
            .group_by(name_counts.c.sender_email)
        ).all()
        for r in best_names:
            name_by_email[str(r.sender_email)] = str(r.sender_name) if r.sender_name is not None else None

    total_emails = db.execute(
        select(func.count()).select_from(EmailMessage).where(EmailMessage.account_id == account_id)
    ).scalar_one()

    domains_rows = db.execute(
        select(
            func.substr(EmailMessage.sender_email, func.instr(EmailMessage.sender_email, "@") + 1).label("domain"),
            func.count().label("count"),
        )
        .where(*base)
        .group_by("domain")
        .order_by(func.count().desc(), "domain")
        .limit(10)
    ).all()

    return {
        "total_emails": total_emails,
        "top_senders": [
            {"email": r.sender_email, "name": name_by_email.get(r.sender_email), "count": int(r.count)} for r in rows
        ],
        "top_domains": [{"domain": r.domain, "count": int(r.count)} for r in domains_rows],
    }


@router.get("/insights/senders/samples")
def sender_message_samples(
    account_id: int,
    sender_email: str,
    limit: int = 5,
    db: Session = Depends(get_db),
) -> dict:
    """
    Recent messages from a single parsed From address, with stored header snapshot
    (if captured during analysis). Useful to see why a mailbox appears as its own top sender.
    """
    lim = max(1, min(limit, 20))
    rows = db.execute(
        select(
            EmailMessage.received_at,
            EmailMessage.subject,
            EmailMessage.sender_name,
            EmailMessage.header_snapshot,
        )
        .where(EmailMessage.account_id == account_id)
        .where(EmailMessage.sender_email == sender_email)
        .order_by(EmailMessage.received_at.desc())
        .limit(lim)
    ).all()

    samples = []
    for r in rows:
        headers: dict[str, str] | None = None
        if r.header_snapshot:
            try:
                raw = json.loads(r.header_snapshot)
                if isinstance(raw, dict):
                    headers = {str(k): str(v) for k, v in raw.items()}
            except (json.JSONDecodeError, TypeError):
                headers = None
        samples.append(
            {
                "received_at": r.received_at.isoformat(),
                "subject": r.subject,
                "sender_name": r.sender_name,
                "headers": headers,
            }
        )

    return {"sender_email": sender_email, "samples": samples}


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
