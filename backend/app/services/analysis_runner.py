from __future__ import annotations

import hashlib
import random
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from sqlalchemy import delete

from app.db.models import AnalysisRun, AnalysisStatus, EmailMessage, ProcessedRange
from app.db.session import SessionLocal


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

            for i in range(run.emails_processed, run.total_emails):
                if cancel.is_set():
                    # Revert partial writes for this run.
                    db.execute(delete(EmailMessage).where(EmailMessage.analysis_run_id == run.id))
                    run.status = AnalysisStatus.cancelled
                    run.finished_at = datetime.utcnow()
                    db.commit()
                    return

                # Persist deterministic stub message metadata so Insights can be real.
                msg = _generate_message(run, index=i)
                msg.analysis_run_id = run.id
                db.add(msg)

                run.emails_processed = i + 1
                db.commit()
                time.sleep(0.03)

            # Mark processed coverage (half-open range).
            db.add(
                ProcessedRange(
                    account_id=run.account_id,
                    start_date=run.start_date,
                    end_date_exclusive=run.end_date_exclusive,
                    emails_count=run.total_emails,
                )
            )
            run.status = AnalysisStatus.completed
            run.finished_at = datetime.utcnow()
            db.commit()
        except Exception as e:
            try:
                run = db.get(AnalysisRun, run_id)
                if run and run.status in (AnalysisStatus.pending, AnalysisStatus.processing):
                    # Revert partial writes for this run.
                    db.execute(delete(EmailMessage).where(EmailMessage.analysis_run_id == run.id))
                    run.status = AnalysisStatus.failed
                    run.error_message = str(e)
                    run.finished_at = datetime.utcnow()
                    db.commit()
            except Exception:
                db.rollback()
        finally:
            db.close()
            with self._lock:
                self._jobs.pop(run_id, None)


runner = InProcessAnalysisRunner()


def _generate_message(run: AnalysisRun, index: int) -> EmailMessage:
    """
    Deterministic pseudo-email generator keyed by run params.
    Creates a stable dataset for insights until provider connectors exist.
    """
    seed_input = f"{run.account_id}:{run.start_date.isoformat()}:{run.end_date_exclusive.isoformat()}:{index}".encode()
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

    span_days = max(1, (run.end_date_exclusive - run.start_date).days)
    offset_days = rng.randrange(0, span_days)
    received_at = datetime.combine(run.start_date, datetime.min.time()) + timedelta(days=offset_days, minutes=rng.randrange(0, 24 * 60))

    return EmailMessage(
        account_id=run.account_id,
        external_id=f"stub:{run.id}:{index}",
        received_at=received_at,
        sender_email=sender_email,
        sender_name=None,
        subject=subject,
        category=cat,
    )

