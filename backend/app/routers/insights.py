from __future__ import annotations

from fastapi import APIRouter


router = APIRouter(tags=["insights"])


@router.get("/insights/summary")
def summary() -> dict:
    return {
        "all_accounts": {"total_accounts": 0, "total_emails": 0, "total_senders": 0},
        "current_account": {"account_emails": 0, "account_senders": 0, "processed_ranges": 0},
    }

