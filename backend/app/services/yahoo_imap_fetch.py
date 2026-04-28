from __future__ import annotations

import email
import imaplib
import json
from dataclasses import dataclass
from datetime import datetime, timezone


_HEADER_KEYS = frozenset(
    {
        "from",
        "to",
        "subject",
        "date",
        "reply-to",
        "return-path",
        "sender",
        "delivered-to",
        "cc",
        "list-id",
        "mailing-list",
        "message-id",
    }
)


@dataclass(frozen=True)
class FetchedMessage:
    external_id: str
    received_at: datetime
    sender_email: str
    sender_name: str | None
    subject: str
    header_snapshot: str | None


class YahooFetchError(Exception):
    pass


def _imap_date(d: datetime) -> str:
    # IMAP uses day-month-year, e.g. 27-Apr-2026
    return d.strftime("%d-%b-%Y")


def fetch_metadata(
    *,
    email_address: str,
    app_password: str,
    start_dt: datetime,
    end_dt: datetime,
    limit: int = 500,
) -> list[FetchedMessage]:
    """
    Minimal Yahoo IMAP metadata fetch.
    Returns headers-only info; does not download bodies.
    """
    if start_dt.tzinfo is None:
        start_dt = start_dt.replace(tzinfo=timezone.utc)
    if end_dt.tzinfo is None:
        end_dt = end_dt.replace(tzinfo=timezone.utc)

    try:
        imap = imaplib.IMAP4_SSL("imap.mail.yahoo.com", 993)
        imap.login(email_address, app_password)
        imap.select("INBOX")

        # IMAP search uses SINCE (inclusive) and BEFORE (exclusive).
        # We approximate with day precision; finer filtering is done client-side after parsing Date.
        since_s = _imap_date(start_dt.astimezone(timezone.utc))
        before_s = _imap_date(end_dt.astimezone(timezone.utc))
        typ, data = imap.search(None, f"(SINCE {since_s} BEFORE {before_s})")
        if typ != "OK":
            raise YahooFetchError("IMAP search failed")

        ids = (data[0] or b"").split()
        # Newest first for UX; limit for safety.
        ids = list(reversed(ids))[:limit]

        out: list[FetchedMessage] = []
        for mid in ids:
            typ, parts = imap.fetch(mid, "(BODY.PEEK[HEADER])")
            if typ != "OK" or not parts:
                continue
            raw = parts[0][1]
            msg = email.message_from_bytes(raw)
            subj = msg.get("Subject", "") or ""
            frm = msg.get("From", "") or ""
            date_hdr = msg.get("Date")

            sender_name, sender_email = email.utils.parseaddr(frm)
            sender_name = sender_name or None
            sender_email = sender_email or ""

            hdrs: dict[str, str] = {}
            for k, v in msg.items():
                lk = k.lower()
                if lk in _HEADER_KEYS and v:
                    hdrs[lk] = v
            header_snapshot = json.dumps(hdrs, ensure_ascii=False) if hdrs else None

            received_at = datetime.utcnow().replace(tzinfo=timezone.utc)
            if date_hdr:
                try:
                    dt = email.utils.parsedate_to_datetime(date_hdr)
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    received_at = dt.astimezone(timezone.utc)
                except Exception:
                    pass

            # Filter by exact timestamps.
            if not (start_dt <= received_at < end_dt):
                continue

            out.append(
                FetchedMessage(
                    external_id=f"imap:{mid.decode(errors='ignore')}",
                    received_at=received_at,
                    sender_email=sender_email,
                    sender_name=sender_name,
                    subject=subj,
                    header_snapshot=header_snapshot,
                )
            )

        return out
    except imaplib.IMAP4.error as e:
        raise YahooFetchError(f"IMAP auth/fetch failed: {e}") from e
    except YahooFetchError:
        raise
    except Exception as e:  # noqa: BLE001
        raise YahooFetchError(str(e)) from e
    finally:
        try:
            imap.logout()  # type: ignore[misc]
        except Exception:
            pass

