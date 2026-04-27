from __future__ import annotations

import hashlib
import random
import threading
import time
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from sqlalchemy import delete
from sqlalchemy.exc import IntegrityError

from app.db.models import AnalysisRun, AnalysisStatus, EmailMessage, ProcessedRange
from app.db.session import SessionLocal

CHUNK_DAYS = 7


@dataclass(frozen=True)
class JobHandle:
    cancel: threading.Event
    thread: threading.Thread


class InProcessAnalysisRunner:
    """
    Minimal local runner:
    - Runs in a background thread
    - Writes progress to the AnalysisRun row
    - Supports cancellation via Event

    This is intentionally simple for local-first MVP. We'll replace it with a
    proper task queue later if needed.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._jobs: dict[int, JobHandle] = {}

    def start(self, run_id: int) -> None:
        with self._lock:
            if run_id in self._jobs:
                return
            cancel = threading.Event()
            t = threading.Thread(target=self._run, args=(run_id, cancel), daemon=True)
            self._jobs[run_id] = JobHandle(cancel=cancel, thread=t)
            t.start()

    def stop(self, run_id: int) -> bool:
        with self._lock:
            handle = self._jobs.get(run_id)
            if not handle:
                return False
            handle.cancel.set()
            return True

    def _run(self, run_id: int, cancel: threading.Event) -> None:
        db: Session = SessionLocal()
        try:
            run = db.get(AnalysisRun, run_id)
            if not run:
                return

            if run.status not in (AnalysisStatus.pending, AnalysisStatus.processing):
                return

            run.status = AnalysisStatus.processing
            run.started_at = run.started_at or datetime.utcnow()

            # Stub total. Replace with real email count once providers exist.
            # Keep it stable/deterministic per run for now.
            if not run.total_emails or run.total_emails <= 0:
                day_span = (run.end_date_exclusive - run.start_date).days
                run.total_emails = max(10, min(500, day_span * 15))
            db.commit()

            chunks = _chunk_ranges(run.start_date, run.end_date_exclusive, days=CHUNK_DAYS)
            chunk_totals = _distribute_total(total=run.total_emails, weights=[(e - s).days for (s, e) in chunks])
            start_index = run.emails_processed
            global_index = 0

            for (chunk_start, chunk_end), chunk_total in zip(chunks, chunk_totals):
                chunk_first_index = global_index
                chunk_last_index_exclusive = global_index + chunk_total
                global_index = chunk_last_index_exclusive

                # Skip chunks already fully processed (e.g., resume-ish behavior if we ever add it).
                if start_index >= chunk_last_index_exclusive:
                    continue

                for i in range(max(start_index, chunk_first_index), chunk_last_index_exclusive):
                    if cancel.is_set():
                        _revert_partial_run(db, run)
                        return

                    msg = _generate_message(run, index=i, chunk_start=chunk_start, chunk_end_exclusive=chunk_end)
                    msg.analysis_run_id = run.id
                    db.add(msg)

                    run.emails_processed = i + 1
                    db.commit()
                    time.sleep(0.03)

                # Mark processed coverage (half-open range) per chunk.
                try:
                    db.add(
                        ProcessedRange(
                            account_id=run.account_id,
                            analysis_run_id=run.id,
                            start_date=chunk_start,
                            end_date_exclusive=chunk_end,
                            emails_count=chunk_total,
                        )
                    )
                    db.commit()
                except IntegrityError:
                    db.rollback()

            run.status = AnalysisStatus.completed
            run.finished_at = datetime.utcnow()
            db.commit()
        except Exception as e:
            try:
                run = db.get(AnalysisRun, run_id)
                if run and run.status in (AnalysisStatus.pending, AnalysisStatus.processing):
                    _revert_partial_run(db, run, failed_error=str(e))
            except Exception:
                db.rollback()
        finally:
            db.close()
            with self._lock:
                self._jobs.pop(run_id, None)


runner = InProcessAnalysisRunner()


def _revert_partial_run(db: Session, run: AnalysisRun, failed_error: str | None = None) -> None:
    # Revert partial writes for this run.
    db.execute(delete(EmailMessage).where(EmailMessage.analysis_run_id == run.id))
    db.execute(delete(ProcessedRange).where(ProcessedRange.analysis_run_id == run.id))
    if failed_error is None:
        run.status = AnalysisStatus.cancelled
    else:
        run.status = AnalysisStatus.failed
        run.error_message = failed_error
    run.finished_at = datetime.utcnow()
    db.commit()


def _chunk_ranges(start_date: date, end_date_exclusive: date, days: int) -> list[tuple[date, date]]:
    if end_date_exclusive <= start_date:
        return []
    if days <= 0:
        return [(start_date, end_date_exclusive)]
    out: list[tuple[date, date]] = []
    cur = start_date
    step = timedelta(days=days)
    while cur < end_date_exclusive:
        nxt = min(end_date_exclusive, cur + step)
        out.append((cur, nxt))
        cur = nxt
    return out


def _distribute_total(total: int, weights: list[int]) -> list[int]:
    if total <= 0:
        return [0 for _ in weights]
    wsum = sum(max(0, w) for w in weights)
    if wsum <= 0:
        # Even distribution if weights are all zero.
        base = total // max(1, len(weights))
        rem = total - base * len(weights)
        return [base + (1 if i < rem else 0) for i in range(len(weights))]

    raw = [total * max(0, w) / wsum for w in weights]
    floors = [int(x) for x in raw]
    rem = total - sum(floors)
    # Largest remainder method
    remainders = sorted([(raw[i] - floors[i], i) for i in range(len(weights))], reverse=True)
    for k in range(rem):
        floors[remainders[k][1]] += 1
    return floors


def _generate_message(
    run: AnalysisRun,
    index: int,
    chunk_start: datetime.date,
    chunk_end_exclusive: datetime.date,
) -> EmailMessage:
    """
    Deterministic pseudo-email generator keyed by run params.
    Creates a stable dataset for insights until provider connectors exist.
    """
    seed_input = (
        f"{run.account_id}:{run.start_date.isoformat()}:{run.end_date_exclusive.isoformat()}:"
        f"{chunk_start.isoformat()}:{chunk_end_exclusive.isoformat()}:{index}".encode()
    )
    seed = int(hashlib.sha256(seed_input).hexdigest()[:8], 16)
    rng = random.Random(seed)

    categories = [
        ("notifications", ["receipt", "confirm", "alert", "reset"]),
        ("newsletters", ["newsletter", "digest", "weekly", "unsubscribe"]),
        ("social", ["mentioned you", "new follower", "commented", "invitation"]),
        ("shopping", ["order", "shipping", "delivered", "invoice"]),
        ("work", ["meeting", "agenda", "project", "action required"]),
        ("personal", ["hi", "catch up", "photos", "dinner"]),
        ("other", ["update", "info", "status", "notice"]),
    ]
    cat, keywords = categories[seed % len(categories)]

    sender_domain = rng.choice(
        [
            "amazon.com",
            "github.com",
            "google.com",
            "newsletter.example",
            "company.com",
            "bank.com",
            "social.example",
        ]
    )
    sender_local = rng.choice(["noreply", "updates", "team", "support", "billing", "friend", "alerts"])
    sender_email = f"{sender_local}@{sender_domain}"

    subject = f"{rng.choice(keywords).title()} #{(seed % 5000) + 1}"

    span_days = max(1, (chunk_end_exclusive - chunk_start).days)
    offset_days = rng.randrange(0, span_days)
    received_at = datetime.combine(chunk_start, datetime.min.time()) + timedelta(
        days=offset_days, minutes=rng.randrange(0, 24 * 60)
    )

    return EmailMessage(
        account_id=run.account_id,
        external_id=f"stub:{run.id}:{index}",
        received_at=received_at,
        sender_email=sender_email,
        sender_name=None,
        subject=subject,
        category=cat,
    )

