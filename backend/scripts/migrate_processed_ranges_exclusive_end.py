"""
Migrate processed_date_ranges.end_date to canonical half-open bounds [start, end).

Two legacy bugs:
  1) end_date at 23:59:59.xxx (inclusive EOD) → next calendar day at 00:00
  2) end_date at 00:00 on the *last covered calendar day* (e.g. 2023-12-31) — wrong.
     Half-open [start, 2023-12-31 00:00) excludes all of Dec 31. The true exclusive
     bound for "through Dec 31" is 2024-01-01 00:00.

2026-01-01 00:00 is already correct as "first day not in range" for through 2025.

Run (from backend/):
  python3 -m scripts.migrate_processed_ranges_exclusive_end --dry-run
  python3 -m scripts.migrate_processed_ranges_exclusive_end --fix-midnight-ends

Without --fix-midnight-ends, only non-midnight EOD rows are updated (original behavior).

Set DATABASE_URL if needed.
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timedelta, time
from pathlib import Path

from sqlalchemy import func

_backend_root = Path(__file__).resolve().parent.parent
if str(_backend_root) not in sys.path:
    sys.path.insert(0, str(_backend_root))


def _abs_sqlite_url(url: str) -> str:
    if not url.startswith("sqlite:///"):
        return url
    raw = url.replace("sqlite:///", "", 1)
    if raw.startswith("./"):
        raw = raw[2:]
    if os.path.isabs(raw):
        return f"sqlite:///{raw}"
    abs_path = str((_backend_root / raw).resolve())
    return f"sqlite:///{abs_path}"


def _prepare_database_url() -> str:
    from dotenv import load_dotenv

    load_dotenv(_backend_root / ".env")
    url = os.getenv("DATABASE_URL", "sqlite:///./data/mailmind.db")
    if url.startswith("sqlite:///"):
        url = _abs_sqlite_url(url)
        os.environ["DATABASE_URL"] = url
    return url


def _legacy_exclusive_end(e: datetime) -> datetime:
    return datetime.combine(e.date(), time.min) + timedelta(days=1)


def _is_canonical_midnight(e: datetime) -> bool:
    return e.hour == 0 and e.minute == 0 and e.second == 0 and e.microsecond == 0


def _emails_on_calendar_day_starting_at(db, account_id: int, day_start: datetime) -> bool:
    from app.database import EmailMetadata  # noqa: E402

    next_morning = day_start + timedelta(days=1)
    q = (
        db.query(EmailMetadata.id)
        .filter(
            EmailMetadata.account_id == account_id,
            EmailMetadata.date_received >= day_start,
            EmailMetadata.date_received < next_morning,
        )
        .limit(1)
    )
    return q.first() is not None


def _proposed_exclusive_end(db, r, fix_midnight: bool) -> datetime | None:
    """
    Return new end_date if this row should change; else None.
    """
    e = r.end_date
    if e is None or e <= r.start_date:
        return None

    # 1) Legacy 23:59…
    if not _is_canonical_midnight(e):
        return _legacy_exclusive_end(e)

    if not fix_midnight:
        return None

    # 2) Trust Jan 1 00:00 as correct exclusive "year after last covered" in most installs
    if e.month == 1 and e.day == 1:
        return None

    # 3) Dec 31 00:00 — almost always "through Dec 31" stored one day short
    if e.month == 12 and e.day == 31:
        return e + timedelta(days=1)

    # 4) Any other midnight: if mail exists that calendar day at/after `e`, data cannot
    #    live in [start, e) — exclusive bound was stored too early; bump one day.
    if _emails_on_calendar_day_starting_at(db, r.account_id, e):
        return e + timedelta(days=1)

    return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate processed_date_ranges to half-open exclusive end_date")
    parser.add_argument("--dry-run", action="store_true", help="Print changes only, do not commit")
    parser.add_argument(
        "--fix-midnight-ends",
        action="store_true",
        help="Fix midnight ends that are one calendar day too early (Dec 31 pattern, "
        "or any day with emails on that day; skips Jan 1 ends).",
    )
    args = parser.parse_args()

    resolved = _prepare_database_url()
    print(f"DATABASE_URL (resolved): {resolved}")

    from app.database import SessionLocal, ProcessedDateRange  # noqa: E402

    db = SessionLocal()
    try:
        rows = db.query(ProcessedDateRange).order_by(ProcessedDateRange.id).all()
        print(f"Rows in processed_date_ranges: {len(rows)}")
        if not rows:
            print("Nothing to migrate (no rows).")
            return

        if not args.fix_midnight_ends:
            print(
                "Note: midnight-only rows are skipped. If 'through' in the UI is one day early "
                "(e.g. ends show through Dec 30 instead of Dec 31), re-run with --fix-midnight-ends."
            )

        updated = 0
        for r in rows:
            new_end = _proposed_exclusive_end(db, r, args.fix_midnight_ends)
            if new_end is None or new_end == r.end_date:
                continue
            print(
                f"  id={r.id} account_id={r.account_id}: end_date {r.end_date!r} -> {new_end!r} "
                f"(UI 'through' ≈ {(new_end - timedelta(days=1)).date()} incl.)"
            )
            if not args.dry_run:
                r.end_date = new_end
            updated += 1

        if updated == 0:
            print("No changes applied for current options.")

        if args.dry_run:
            print(f"Dry run: would update {updated} row(s). Re-run without --dry-run to apply.")
            db.rollback()
        else:
            db.commit()
            print(f"Migration complete: updated {updated} of {len(rows)} row(s).")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
