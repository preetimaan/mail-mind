from __future__ import annotations

import json
from collections import Counter
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import (
    CUSTOM_LABELS,
    ClassificationConfidence,
    ClassificationSource,
    EmailMessage,
    SenderClassification,
)
from app.db.session import get_db
from app.services.ai_classifier import AIClassifierError, classify_sender
from app.services.classification_engine import classify_account, manual_classify
from app.settings import get_settings

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
    classified_senders = 0
    unclassified_emails = 0
    unclassified_senders = 0

    for row in rows:
        labels: list[str] = json.loads(row.custom_labels or "[]")
        count = int(row.email_count)
        if labels:
            classified_senders += 1
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
        "classified_senders": classified_senders,
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
                "label_sources": json.loads(getattr(row, "label_sources", None) or "{}"),
                "email_count": row.email_count,
                "confidence": row.confidence,
                "source": row.source,
                "sample_subjects": json.loads(row.sample_subjects or "[]"),
                "suggested_gmail_labels": json.loads(getattr(row, "suggested_gmail_labels", None) or "[]"),
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
    limit: int = 500,
    db: Session = Depends(get_db),
) -> dict:
    """
    Returns senders with no custom label assigned, sorted by email volume.
    These are candidates for manual assignment or AI enhancement.
    """
    rows = db.execute(
        select(SenderClassification)
        .where(SenderClassification.account_id == account_id)
        .where(
            (SenderClassification.custom_labels == "[]")
            | (SenderClassification.custom_labels == "")
            | SenderClassification.custom_labels.is_(None)
        )
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
            "suggested_gmail_labels": json.loads(getattr(row, "suggested_gmail_labels", None) or "[]"),
        }
        for row in rows
    ]

    return {"senders": results, "total": len(results)}


# ---------------------------------------------------------------------------
# Manual label assignment
# ---------------------------------------------------------------------------

class ManualClassifyRequest(BaseModel):
    sender_email: str
    custom_labels: list[str]


class GmailLabelSuggestionRequest(BaseModel):
    sender_email: str
    gmail_labels: list[str]


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
# AI enhancement — classify unclassified senders via Gemini or OpenAI
# ---------------------------------------------------------------------------

@router.post("/label-suggestions/classify/gmail-labels")
def set_gmail_labels(
    account_id: int,
    body: GmailLabelSuggestionRequest,
    db: Session = Depends(get_db),
) -> dict:
    """
    Associate existing Gmail label names with a sender for filter suggestion purposes.
    Does not create any Gmail labels — purely a local annotation.
    """
    sc = db.execute(
        select(SenderClassification).where(
            SenderClassification.account_id == account_id,
            SenderClassification.sender_email == body.sender_email,
        )
    ).scalar_one_or_none()

    if not sc:
        raise HTTPException(status_code=404, detail="Sender not found. Run classification first.")

    sc.suggested_gmail_labels = json.dumps(body.gmail_labels)
    db.commit()
    return {"sender_email": sc.sender_email, "suggested_gmail_labels": body.gmail_labels}


@router.post("/label-suggestions/ai-enhance")
def ai_enhance(account_id: int, db: Session = Depends(get_db)) -> dict:
    """
    Runs the configured AI provider over all unclassified senders.
    Requires MAILMIND_AI_PROVIDER and MAILMIND_AI_API_KEY to be set.
    Only sends sender name, domain, and subject lines — no email bodies.
    Results are cached; the same sender is never sent to the AI again.
    """
    settings = get_settings()
    provider = settings.ai_provider
    api_key = settings.ai_api_key

    if not provider or not api_key:
        raise HTTPException(
            status_code=400,
            detail=(
                "AI provider not configured. Set MAILMIND_AI_PROVIDER (gemini or openai) "
                "and MAILMIND_AI_API_KEY in your .env file."
            ),
        )

    # Fetch unclassified senders only.
    rows = db.execute(
        select(SenderClassification)
        .where(SenderClassification.account_id == account_id)
        .order_by(SenderClassification.email_count.desc())
    ).scalars().all()

    unclassified = [
        r for r in rows
        if not json.loads(r.custom_labels or "[]")
        and r.source != ClassificationSource.ai.value
    ]

    now = datetime.utcnow()
    processed = 0
    errors = 0

    for sc in unclassified:
        subjects = json.loads(sc.sample_subjects or "[]")
        try:
            labels = classify_sender(
                provider=provider,
                api_key=api_key,
                sender_email=sc.sender_email,
                sender_name=sc.sender_name,
                sample_subjects=subjects,
            )
        except AIClassifierError:
            errors += 1
            continue

        sc.custom_labels = json.dumps(labels)
        sc.confidence = ClassificationConfidence.medium.value
        sc.source = ClassificationSource.ai.value
        sc.classified_at = now
        processed += 1

    db.commit()

    return {
        "processed": processed,
        "errors": errors,
        "provider": provider,
    }


# ---------------------------------------------------------------------------
# AI config status (lets the UI know whether AI is available)
# ---------------------------------------------------------------------------

@router.get("/label-suggestions/ai-status")
def ai_status() -> dict:
    settings = get_settings()
    configured = bool(settings.ai_provider and settings.ai_api_key)
    return {
        "configured": configured,
        "provider": settings.ai_provider if configured else None,
    }


# ---------------------------------------------------------------------------
# Available labels (for the UI to populate dropdowns)
# ---------------------------------------------------------------------------

@router.get("/label-suggestions/labels")
def available_labels() -> dict:
    return {"labels": CUSTOM_LABELS}


# ---------------------------------------------------------------------------
# Filter queries — collapsed per-label Gmail search strings
# ---------------------------------------------------------------------------

# Free/shared email provider domains — never collapse to @domain because the
# domain doesn't identify an organisation (everyone has a gmail.com address).
_SHARED_EMAIL_DOMAINS = {
    "gmail.com", "yahoo.com", "yahoo.co.uk", "yahoo.com.au",
    "hotmail.com", "hotmail.co.uk", "outlook.com", "live.com",
    "icloud.com", "me.com", "mac.com",
    "protonmail.com", "pm.me", "proton.me",
    "aol.com", "msn.com", "ymail.com", "googlemail.com",
}


@router.get("/label-suggestions/filter-queries")
def filter_queries(account_id: int, db: Session = Depends(get_db)) -> dict:
    """
    Returns a Gmail-compatible `from:` query per custom label.
    Domains with multiple classified senders are collapsed to @domain.com,
    except for shared email providers (gmail.com, yahoo.com, etc.) where
    exact addresses are always used to avoid over-broad filters.
    """
    rows = db.execute(
        select(SenderClassification)
        .where(SenderClassification.account_id == account_id)
    ).scalars().all()

    label_senders: dict[str, list[SenderClassification]] = {label: [] for label in CUSTOM_LABELS}
    for row in rows:
        labels: list[str] = json.loads(row.custom_labels or "[]")
        for label in labels:
            if label in label_senders:
                label_senders[label].append(row)

    results = []
    for label in CUSTOM_LABELS:
        senders = label_senders[label]
        if not senders:
            results.append({"label": label, "query": "", "sender_count": 0})
            continue

        domain_counts = Counter(s.sender_domain for s in senders if s.sender_domain)
        parts: list[str] = []
        covered: set[str] = set()

        for domain, count in domain_counts.items():
            if count > 1 and domain not in _SHARED_EMAIL_DOMAINS:
                parts.append(f"@{domain}")
                for s in senders:
                    if s.sender_domain == domain:
                        covered.add(s.sender_email)

        for s in senders:
            if s.sender_email not in covered:
                parts.append(s.sender_email)

        if not parts:
            query = ""
        elif len(parts) == 1:
            query = f"from:{parts[0]}"
        else:
            query = "from:(" + " OR ".join(parts) + ")"

        # Collect all unique Gmail label suggestions across senders for this custom label.
        gmail_label_set: list[str] = []
        seen: set[str] = set()
        for s in senders:
            for gl in json.loads(getattr(s, "suggested_gmail_labels", None) or "[]"):
                if gl not in seen:
                    gmail_label_set.append(gl)
                    seen.add(gl)

        results.append({
            "label": label,
            "query": query,
            "sender_count": len(senders),
            "suggested_gmail_labels": gmail_label_set,
        })

    return {"queries": results}
