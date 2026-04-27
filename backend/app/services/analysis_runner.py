from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from sqlalchemy import delete
from sqlalchemy.exc import IntegrityError

from app.db.models import AnalysisRun, AnalysisStatus, EmailAccount, EmailMessage, ProcessedRange, Provider
from app.db.session import SessionLocal
from app.services.credential_store import get_gmail_tokens, get_yahoo_app_password, set_gmail_tokens
from app.services.gmail_api_fetch import GmailFetchError, get_message_metadata, list_message_ids
from app.services.gmail_token_refresh import GmailRefreshError, refresh_access_token
from app.services.yahoo_imap_fetch import YahooFetchError, fetch_metadata
from app.settings import get_settings

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

            settings = get_settings()
            account = db.get(EmailAccount, run.account_id)
            if not account:
                raise RuntimeError("Account not found for run")

            # Real provider fetching:
            # - Gmail: Gmail API metadata
            # - Yahoo: IMAP header metadata
            # Total emails is estimated as "messages discovered" for now.
            if not run.total_emails or run.total_emails <= 0:
                run.total_emails = 0
            db.commit()

            chunks = _chunk_ranges(run.start_date, run.end_date_exclusive, days=CHUNK_DAYS)
            for (chunk_start, chunk_end) in chunks:
                if cancel.is_set():
                    _revert_partial_run(db, run)
                    return

                start_dt = datetime.combine(chunk_start, datetime.min.time())
                end_dt = datetime.combine(chunk_end, datetime.min.time())

                fetched_count = 0

                if account.provider == Provider.yahoo:
                    pw = get_yahoo_app_password(db, settings, account.id)
                    if not pw:
                        raise RuntimeError("Yahoo credentials missing")
                    try:
                        metas = fetch_metadata(
                            email_address=account.email,
                            app_password=pw,
                            start_dt=start_dt,
                            end_dt=end_dt,
                            limit=500,
                        )
                    except YahooFetchError as e:
                        account.is_active = False
                        db.commit()
                        raise RuntimeError(f"Yahoo fetch failed: {e}") from e

                    for m in metas:
                        if cancel.is_set():
                            _revert_partial_run(db, run)
                            return
                        db.add(
                            EmailMessage(
                                account_id=account.id,
                                analysis_run_id=run.id,
                                external_id=m.external_id,
                                received_at=m.received_at.replace(tzinfo=None),
                                sender_email=m.sender_email,
                                sender_name=m.sender_name,
                                subject=m.subject,
                                category="other",
                            )
                        )
                        fetched_count += 1
                        run.emails_processed += 1
                        db.commit()
                        time.sleep(0.01)

                elif account.provider == Provider.gmail:
                    tokens = get_gmail_tokens(db, settings, account.id)
                    if not tokens:
                        raise RuntimeError("Gmail credentials missing")

                    access_token = tokens.access_token
                    try:
                        ids = list_message_ids(access_token=access_token, start_dt=start_dt, end_dt=end_dt, max_results=500)
                    except GmailFetchError as e:
                        if str(e) == "unauthorized" and tokens.refresh_token and settings.gmail_client_id and settings.gmail_client_secret:
                            try:
                                refreshed = refresh_access_token(
                                    client_id=settings.gmail_client_id,
                                    client_secret=settings.gmail_client_secret,
                                    refresh_token=tokens.refresh_token,
                                )
                                access_token = refreshed.access_token
                                set_gmail_tokens(
                                    db,
                                    settings,
                                    account.id,
                                    access_token=access_token,
                                    refresh_token=tokens.refresh_token,
                                    expires_at=refreshed.expires_at,
                                    scope=refreshed.scope or tokens.scope,
                                    token_type=refreshed.token_type or tokens.token_type,
                                )
                                db.commit()
                                ids = list_message_ids(
                                    access_token=access_token, start_dt=start_dt, end_dt=end_dt, max_results=500
                                )
                            except (GmailRefreshError, GmailFetchError) as e2:
                                account.is_active = False
                                db.commit()
                                raise RuntimeError(f"Gmail auth failed: {e2}") from e2
                        else:
                            account.is_active = False
                            db.commit()
                            raise RuntimeError(f"Gmail fetch failed: {e}") from e

                    for mid in ids:
                        if cancel.is_set():
                            _revert_partial_run(db, run)
                            return
                        try:
                            meta = get_message_metadata(access_token=access_token, message_id=mid)
                        except GmailFetchError as e:
                            if str(e) == "unauthorized":
                                account.is_active = False
                                db.commit()
                                raise RuntimeError("Gmail token expired/unauthorized") from e
                            continue

                        from_hdr = meta.headers.get("from", "")
                        sender_name, sender_email = _parse_from(from_hdr)
                        subject = meta.headers.get("subject", "") or ""
                        received_at = datetime.utcnow()
                        if meta.internal_date_ms is not None:
                            received_at = datetime.utcfromtimestamp(meta.internal_date_ms / 1000.0)

                        db.add(
                            EmailMessage(
                                account_id=account.id,
                                analysis_run_id=run.id,
                                external_id=f"gmail:{meta.id}",
                                received_at=received_at,
                                sender_email=sender_email,
                                sender_name=sender_name,
                                subject=subject,
                                category="other",
                            )
                        )
                        fetched_count += 1
                        run.emails_processed += 1
                        db.commit()
                        time.sleep(0.01)

                # Update total_emails as we discover messages.
                run.total_emails += fetched_count
                db.commit()

                try:
                    db.add(
                        ProcessedRange(
                            account_id=run.account_id,
                            analysis_run_id=run.id,
                            start_date=chunk_start,
                            end_date_exclusive=chunk_end,
                            emails_count=fetched_count,
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


def _parse_from(from_header: str) -> tuple[str | None, str]:
    """
    Tiny parser for "Name <email@x>".
    Keeps this dependency-free; we can swap to email.utils later if needed.
    """
    s = (from_header or "").strip()
    if "<" in s and ">" in s:
        name = s.split("<", 1)[0].strip().strip('"') or None
        addr = s.split("<", 1)[1].split(">", 1)[0].strip()
        return name, addr
    return None, s

