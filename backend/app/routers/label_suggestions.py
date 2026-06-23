from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import (
    CUSTOM_LABELS,
    EmailMessage,
    SenderClassification,
)
from app.db.session import get_db
from app.services.classification_engine import classify_account, manual_classify

router = APIRouter(tags=["label-suggestions"])


# ---------------------------------------------------------------------------
# Run classification
# ---------------------------------------------------------------------------

@router.post("/label-suggestions/classify")
def run_classification(account_id: int, db: Session = Depends(get_db)) -> dict:
    """
    Trigger the rule-based classification engine for an account.
    Idempotent — safe to re-run; never overwrites manual or AI assignments.
    """
    result = classify_account(account_id=account_id, db=db)
    return result


# ---------------------------------------------------------------------------
# Summary: per-label email + sender counts
# ---------------------------------------------------------------------------

@router.get("/label-suggestions/summary")
def label_summary(account_id: int, db: Session = Depends(get_db)) -> dict:
    """
    Returns coverage stats per custom label and an unclassified count.
    Each SenderClassification row can carry up to 3 labels; we fan-out
    the email_count to each label it belongs to.
    """
    rows = db.execute(
        select(
            SenderClassification.custom_labels,
            SenderClassification.email_count,
        ).where(SenderClassification.account_id == account_id)
    ).all()

    total_emails = db.execute(
        select(func.count())
        .select_from(EmailMessage)
        .where(EmailMessage.account_id == account_id)
    ).scalar_one()

    label_stats: dict[str, dict] = {
        label: {"label": label, "email_count": 0, "sender_count": 0}
        for label in CUSTOM_LABELS
    }
    unclassified_emails = 0
    unclassified_senders = 0

    for row in rows:
        labels: list[str] = json.loads(row.custom_labels or "[]")
        count = int(row.email_count)
        if labels:
            for label in labels:
                if label in label_stats:
                    label_stats[label]["email_count"] += count
                    label_stats[label]["sender_count"] += 1
        else:
            unclassified_emails += count
            unclassified_senders += 1

    coverage_pct = (
        round((total_emails - unclassified_emails) / total_emails * 100, 1)
        if total_emails
        else 0.0
    )

    return {
        "total_emails": total_emails,
        "coverage_percent": coverage_pct,
        "labels": list(label_stats.values()),
        "unclassified": {
            "email_count": unclassified_emails,
            "sender_count": unclassified_senders,
        },
    }


# ---------------------------------------------------------------------------
# Senders for a specific label
# ---------------------------------------------------------------------------

@router.get("/label-suggestions/senders")
def senders_for_label(
    account_id: int,
    label: str,
    limit: int = 50,
    db: Session = Depends(get_db),
) -> dict:
    """
    Returns senders classified under a given custom label, sorted by email volume.
    """
    if label not in CUSTOM_LABELS:
        raise HTTPException(status_code=400, detail=f"Unknown label: {label}. Valid: {CUSTOM_LABELS}")

    rows = db.execute(
        select(SenderClassification)
        .where(SenderClassification.account_id == account_id)
        .order_by(SenderClassification.email_count.desc())
        .limit(500)
    ).scalars().all()

    results = []
    for row in rows:
        labels = json.loads(row.custom_labels or "[]")
        if label in labels:
            results.append({
                "sender_email": row.sender_email,
                "sender_name": row.sender_name,
                "sender_domain": row.sender_domain,
                "custom_labels": labels,
                "email_count": row.email_count,
                "confidence": row.confidence,
                "source": row.source,
                "sample_subjects": json.loads(row.sample_subjects or "[]"),
            })
            if len(results) >= limit:
                break

    return {"label": label, "senders": results, "total": len(results)}


# ---------------------------------------------------------------------------
# Unclassified senders
# ---------------------------------------------------------------------------

@router.get("/label-suggestions/unclassified")
def unclassified_senders(
    account_id: int,
    limit: int = 100,
    db: Session = Depends(get_db),
) -> dict:
    """
    Returns senders with no custom label assigned, sorted by email volume.
    These are candidates for manual assignment or AI enhancement.
    """
    rows = db.execute(
        select(SenderClassification)
        .where(SenderClassification.account_id == account_id)
        .order_by(SenderClassification.email_count.desc())
        .limit(limit)
    ).scalars().all()

    results = [
        {
            "sender_email": row.sender_email,
            "sender_name": row.sender_name,
            "sender_domain": row.sender_domain,
            "email_count": row.email_count,
            "sample_subjects": json.loads(row.sample_subjects or "[]"),
        }
        for row in rows
        if not json.loads(row.custom_labels or "[]")
    ]

    return {"senders": results, "total": len(results)}


# ---------------------------------------------------------------------------
# Manual label assignment
# ---------------------------------------------------------------------------

class ManualClassifyRequest(BaseModel):
    sender_email: str
    custom_labels: list[str]


@router.post("/label-suggestions/classify/manual")
def manual_classify_sender(
    account_id: int,
    body: ManualClassifyRequest,
    db: Session = Depends(get_db),
) -> dict:
    """
    Assign custom labels to a sender manually. Always takes priority over
    rule-based and AI classifications. Pass an empty list to clear labels.
    """
    invalid = [l for l in body.custom_labels if l not in CUSTOM_LABELS]
    if invalid:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown labels: {invalid}. Valid: {CUSTOM_LABELS}",
        )
    if len(body.custom_labels) > 3:
        raise HTTPException(status_code=400, detail="Maximum 3 labels per sender.")

    sc = manual_classify(
        account_id=account_id,
        sender_email=body.sender_email,
        custom_labels=body.custom_labels,
        db=db,
    )
    return {
        "sender_email": sc.sender_email,
        "custom_labels": json.loads(sc.custom_labels),
        "source": sc.source,
    }


# ---------------------------------------------------------------------------
# Available labels (for the UI to populate dropdowns)
# ---------------------------------------------------------------------------

@router.get("/label-suggestions/labels")
def available_labels() -> dict:
    return {"labels": CUSTOM_LABELS}
