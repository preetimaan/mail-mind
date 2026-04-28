from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

import httpx


# System labels we skip so "top senders" is not dominated by the user's own From on sent/draft mail.
GMAIL_ANALYSIS_SKIP_LABELS = frozenset({"SENT", "DRAFT"})


@dataclass(frozen=True)
class GmailMessageMeta:
    id: str
    internal_date_ms: int | None
    headers: dict[str, str]
    label_ids: frozenset[str]


class GmailFetchError(Exception):
    pass


def _gmail_date_q(dt: datetime) -> str:
    # Gmail query uses YYYY/MM/DD
    return dt.astimezone(timezone.utc).strftime("%Y/%m/%d")


def list_message_ids(
    *,
    access_token: str,
    start_dt: datetime,
    end_dt: datetime,
    max_results: int = 500,
) -> list[str]:
    # Date window only would include Sent/Drafts (From is usually the account), inflating self as a "top sender".
    q = f"after:{_gmail_date_q(start_dt)} before:{_gmail_date_q(end_dt)} -in:sent -in:drafts"
    ids: list[str] = []
    page_token: str | None = None
    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        with httpx.Client(timeout=20.0) as client:
            while True:
                params = {"q": q, "maxResults": min(500, max_results - len(ids))}
                if page_token:
                    params["pageToken"] = page_token
                res = client.get("https://gmail.googleapis.com/gmail/v1/users/me/messages", headers=headers, params=params)
                if res.status_code == 401:
                    raise GmailFetchError("unauthorized")
                if res.status_code >= 400:
                    raise GmailFetchError(res.text)
                payload = res.json()
                for m in payload.get("messages", []) or []:
                    mid = m.get("id")
                    if mid:
                        ids.append(mid)
                        if len(ids) >= max_results:
                            return ids
                page_token = payload.get("nextPageToken")
                if not page_token:
                    return ids
    except GmailFetchError:
        raise
    except Exception as e:  # noqa: BLE001
        raise GmailFetchError(str(e)) from e


def get_message_metadata(*, access_token: str, message_id: str) -> GmailMessageMeta:
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {
        "format": "metadata",
        "metadataHeaders": [
            "From",
            "To",
            "Subject",
            "Date",
            "Reply-To",
            "Return-Path",
            "Sender",
            "Delivered-To",
            "Cc",
            "List-Id",
            "Mailing-List",
            "Message-ID",
        ],
    }
    try:
        with httpx.Client(timeout=20.0) as client:
            res = client.get(
                f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{message_id}",
                headers=headers,
                params=params,
            )
        if res.status_code == 401:
            raise GmailFetchError("unauthorized")
        if res.status_code >= 400:
            raise GmailFetchError(res.text)
        payload = res.json()
        hdrs: dict[str, str] = {}
        for h in payload.get("payload", {}).get("headers", []) or []:
            name = h.get("name")
            value = h.get("value")
            if name and value:
                hdrs[name.lower()] = value
        raw_labels = payload.get("labelIds")
        label_ids = frozenset(str(x) for x in raw_labels) if isinstance(raw_labels, list) else frozenset()
        return GmailMessageMeta(
            id=payload.get("id") or message_id,
            internal_date_ms=int(payload["internalDate"]) if payload.get("internalDate") else None,
            headers=hdrs,
            label_ids=label_ids,
        )
    except GmailFetchError:
        raise
    except Exception as e:  # noqa: BLE001
        raise GmailFetchError(str(e)) from e

