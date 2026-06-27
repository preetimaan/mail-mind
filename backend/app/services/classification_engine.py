from __future__ import annotations

import json
import re
from datetime import datetime

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.db.models import (
    CUSTOM_LABELS,  # noqa: F401 — re-exported for router use
    ClassificationConfidence,
    ClassificationSource,
    EmailMessage,
    SenderClassification,
)

LABEL_CAREER = "Career"
LABEL_STUDY = "Study"
LABEL_SOFTWARE = "Software"
LABEL_LIFE_ADMIN = "Life Admin"
LABEL_MONEY = "Money"
LABEL_HEALTH = "Health"
LABEL_GOV_TAX = "Gov & Tax"

# ---------------------------------------------------------------------------
# Tier 1 — known sender domain lists (high confidence, single signal enough)
# ---------------------------------------------------------------------------

# Each entry maps a domain suffix to one or more labels.
# Checked via endswith() so subdomains are covered (e.g. mail.linkedin.com).

_TIER1_DOMAINS: list[tuple[tuple[str, ...], list[str]]] = [
    # Career — job platforms and recruiters
    (
        (
            "linkedin.com",
            "indeed.com",
            "glassdoor.com",
            "greenhouse.io",
            "lever.co",
            "workday.com",
            "smartrecruiters.com",
            "jobvite.com",
            "ziprecruiter.com",
            "dice.com",
            "monster.com",
            "wellfound.com",
            "angellist.com",
            "myworkdayjobs.com",
            "icims.com",
            "taleo.net",
            "brassring.com",
            "successfactors.com",
        ),
        [LABEL_CAREER],
    ),
    # Study — ed-tech and skill platforms
    (
        (
            "udemy.com",
            "coursera.org",
            "pluralsight.com",
            "codecademy.com",
            "leetcode.com",
            "hackerrank.com",
            "edx.org",
            "udacity.com",
            "skillshare.com",
            "duolingo.com",
            "khanacademy.org",
            "datacamp.com",
            "frontendmasters.com",
            "egghead.io",
            "educative.io",
            "interviewbit.com",
            "brilliant.org",
            "oreilly.com",
            "manning.com",
        ),
        [LABEL_STUDY],
    ),
    # Software — developer tools, SaaS, and software services
    (
        (
            "github.com",
            "gitlab.com",
            "bitbucket.org",
            "atlassian.com",
            "notion.so",
            "slack.com",
            "linear.app",
            "clickup.com",
            "asana.com",
            "monday.com",
            "trello.com",
            "basecamp.com",
            "figma.com",
            "canva.com",
            "vercel.com",
            "netlify.com",
            "heroku.com",
            "digitalocean.com",
            "render.com",
            "railway.app",
            "fly.io",
            "sentry.io",
            "datadog.com",
            "newrelic.com",
            "pagerduty.com",
            "cloudflare.com",
            "jetbrains.com",
            "1password.com",
            "lastpass.com",
            "bitwarden.com",
            "zapier.com",
            "airtable.com",
            "calendly.com",
            "typeform.com",
            "hubspot.com",
            "salesforce.com",
            "zendesk.com",
            "intercom.io",
            "mailchimp.com",
            "sendgrid.com",
            "twilio.com",
            "stripe.com",
            "npmjs.com",
            "docker.com",
        ),
        [LABEL_SOFTWARE],
    ),
    # Health — insurers, pharmacies, patient portals
    (
        (
            "aetna.com",
            "cigna.com",
            "humana.com",
            "unitedhealthcare.com",
            "uhc.com",
            "kaiserpermanente.org",
            "bcbs.com",
            "anthem.com",
            "bluecrossca.com",
            "hcsc.net",
            "cvs.com",
            "walgreens.com",
            "riteaid.com",
            "costcopharma.com",
            "zocdoc.com",
            "mychart.com",
            "athenahealth.com",
            "optum.com",
            "caremark.com",
            "express-scripts.com",
        ),
        [LABEL_HEALTH],
    ),
    # Gov & Tax — tax software (gov TLD handled separately)
    (
        (
            "turbotax.com",
            "intuit.com",
            "hrblock.com",
            "taxact.com",
            "freetaxusa.com",
            "taxslayer.com",
            "taxhawk.com",
            "1040.com",
        ),
        [LABEL_GOV_TAX],
    ),
    # Money — banking, fintech, investment
    (
        (
            "chase.com",
            "bankofamerica.com",
            "wellsfargo.com",
            "citibank.com",
            "citi.com",
            "usbank.com",
            "discover.com",
            "capitalone.com",
            "americanexpress.com",
            "amex.com",
            "synchrony.com",
            "navyfederal.org",
            "ally.com",
            "marcus.com",
            "paypal.com",
            "venmo.com",
            "stripe.com",
            "square.com",
            "cash.app",
            "cashapp.com",
            "zelle.com",
            "wise.com",
            "fidelity.com",
            "vanguard.com",
            "schwab.com",
            "robinhood.com",
            "etrade.com",
            "tdameritrade.com",
            "merrilledge.com",
            "creditkarma.com",
            "experian.com",
            "equifax.com",
            "transunion.com",
            "mint.com",
            "nerdwallet.com",
        ),
        [LABEL_MONEY],
    ),
    # Life Admin — delivery carriers and property management globals
    (
        (
            "usps.com",
            "ups.com",
            "fedex.com",
            "dhl.com",
            "uspsdelivers.com",
        ),
        [LABEL_LIFE_ADMIN],
    ),
]


def _tier1_labels(domain: str) -> list[str] | None:
    """Return label list if domain matches a known Tier 1 entry, else None."""
    domain = domain.lower()
    # .gov TLD → Gov & Tax (covers irs.gov, ssa.gov, state.gov, etc.)
    if domain.endswith(".gov"):
        return [LABEL_GOV_TAX]
    for suffixes, labels in _TIER1_DOMAINS:
        for suffix in suffixes:
            if domain == suffix or domain.endswith("." + suffix):
                return labels
    return None


# ---------------------------------------------------------------------------
# Tier 2 — subject keyword patterns (medium confidence)
# ---------------------------------------------------------------------------

_KEYWORD_PATTERNS: list[tuple[re.Pattern[str], list[str]]] = [
    (
        re.compile(
            r"\b(interview|offer letter|offer accepted|background check|"
            r"payslip|pay stub|paystub|salary slip|earnings statement|"
            r"employment verification|job offer|application received|"
            r"application status|we received your application|"
            r"your application|recruiter|new job|job alert)\b",
            re.IGNORECASE,
        ),
        [LABEL_CAREER],
    ),
    (
        re.compile(
            r"\b(course|lesson|certificate|certification|enrollment|"
            r"quiz|assignment|module|learning path|new course|"
            r"your progress|complete your course|skill|workshop|"
            r"webinar|tutorial)\b",
            re.IGNORECASE,
        ),
        [LABEL_STUDY],
    ),
    (
        re.compile(
            r"\b(new release|release notes|changelog|version \d|"
            r"feature update|product update|deployment|build failed|"
            r"build passed|pipeline|pull request|repository|workspace|"
            r"your trial|trial expired|upgrade your plan|"
            r"new in |what.s new in )\b",
            re.IGNORECASE,
        ),
        [LABEL_SOFTWARE],
    ),
    (
        re.compile(
            r"\b(appointment|prescription|lab results?|test results?|"
            r"medical|health|doctor|patient|EOB|explanation of benefits|"
            r"insurance claim|claim status|copay|co-pay|deductible|"
            r"benefits summary|healthcare|referral|diagnosis)\b",
            re.IGNORECASE,
        ),
        [LABEL_HEALTH],
    ),
    (
        re.compile(
            r"\b(tax return|tax refund|tax filing|tax document|"
            r"W-2|W2|1099|1040|IRS|social security|SSA|medicare|"
            r"passport|driver.?s license|voter registration|ballot|"
            r"DMV|department of motor|government benefit|FAFSA|"
            r"unemployment|benefit payment)\b",
            re.IGNORECASE,
        ),
        [LABEL_GOV_TAX],
    ),
    (
        re.compile(
            r"\b(invoice|receipt|payment received|payment confirmed|"
            r"subscription renewed|renewal|billing statement|"
            r"transaction|your order|order confirmation|order shipped|"
            r"statement ready|account statement|direct deposit|"
            r"wire transfer|refund processed|charge|auto-pay)\b",
            re.IGNORECASE,
        ),
        [LABEL_MONEY],
    ),
    (
        re.compile(
            r"\b(rent|lease|landlord|utility bill|utilities|"
            r"electricity bill|gas bill|water bill|internet bill|"
            r"phone bill|service outage|maintenance request|"
            r"HOA|homeowners association|move-?in|move-?out|"
            r"security deposit|property)\b",
            re.IGNORECASE,
        ),
        [LABEL_LIFE_ADMIN],
    ),
]


def _tier2_labels_from_subjects(subjects: list[str]) -> list[str] | None:
    """
    Match keyword patterns against a list of subject lines.
    Returns the union of matched labels if any pattern fires, else None.
    Confidence is medium — requires the caller to store source=tier2_keyword.
    """
    matched: set[str] = set()
    for subject in subjects:
        for pattern, labels in _KEYWORD_PATTERNS:
            if pattern.search(subject):
                matched.update(labels)
    return list(matched) if matched else None


# ---------------------------------------------------------------------------
# Tier 2 — header signals (medium confidence)
# ---------------------------------------------------------------------------

def _tier2_labels_from_headers(header_snapshots: list[str | None]) -> list[str] | None:
    """
    Check stored header JSON snapshots for mailing-list signals.
    List-Id or Mailing-List header presence indicates bulk/newsletter mail
    but does NOT map to a custom label — it's a secondary signal used to
    mark the sender as automated (no custom label assigned, left unclassified
    so the standard Gmail categories cover it).
    Returns None always for now; reserved for future header-based rules.
    """
    return None


# ---------------------------------------------------------------------------
# Automated sender detection (reused from insights.py pattern)
# ---------------------------------------------------------------------------

_AUTOMATED_PATTERNS = re.compile(
    r"(noreply|no-reply|no_reply|donotreply|do-not-reply|"
    r"mailer-daemon|postmaster|bounce|notification|automated)",
    re.IGNORECASE,
)


def _is_automated_sender(sender_email: str) -> bool:
    local = sender_email.split("@")[0] if "@" in sender_email else sender_email
    return bool(_AUTOMATED_PATTERNS.search(local))


# ---------------------------------------------------------------------------
# Main classification function
# ---------------------------------------------------------------------------

def classify_account(account_id: int, db: Session) -> dict:
    """
    Run the full classification pass for all senders in an account.
    Upserts into sender_classifications. Returns a summary dict.
    """
    # Collect all unique senders with their aggregate data.
    rows = db.execute(
        select(
            EmailMessage.sender_email,
            func.max(EmailMessage.sender_name).label("sender_name"),
            func.count().label("email_count"),
        )
        .where(EmailMessage.account_id == account_id)
        .where(EmailMessage.sender_email != "")
        .group_by(EmailMessage.sender_email)
    ).all()

    total = len(rows)
    classified = 0
    unclassified = 0
    now = datetime.utcnow()

    for row in rows:
        sender_email: str = row.sender_email
        sender_name: str | None = row.sender_name
        email_count: int = int(row.email_count)

        domain = sender_email.split("@")[1].lower() if "@" in sender_email else ""

        # Fetch sample subjects for this sender (up to 5 most recent).
        subject_rows = db.execute(
            select(EmailMessage.subject)
            .where(EmailMessage.account_id == account_id)
            .where(EmailMessage.sender_email == sender_email)
            .order_by(EmailMessage.received_at.desc())
            .limit(5)
        ).scalars().all()
        sample_subjects = [s for s in subject_rows if s]

        custom_labels: list[str] = []
        confidence: ClassificationConfidence | None = None
        source: ClassificationSource | None = None

        # --- Tier 1: domain lookup ---
        tier1 = _tier1_labels(domain)
        if tier1:
            custom_labels = tier1[:3]
            confidence = ClassificationConfidence.high
            source = ClassificationSource.tier1_domain

        # --- Tier 2: subject keywords (only if Tier 1 missed) ---
        if not custom_labels and sample_subjects:
            tier2 = _tier2_labels_from_subjects(sample_subjects)
            if tier2:
                custom_labels = tier2[:3]
                confidence = ClassificationConfidence.medium
                source = ClassificationSource.tier2_keyword

        if custom_labels:
            classified += 1
        else:
            unclassified += 1

        # Upsert into sender_classifications.
        existing = db.execute(
            select(SenderClassification).where(
                SenderClassification.account_id == account_id,
                SenderClassification.sender_email == sender_email,
            )
        ).scalar_one_or_none()

        if existing:
            # Only overwrite manual/ai classifications if source is higher confidence.
            if existing.source not in (
                ClassificationSource.manual,
                ClassificationSource.ai,
            ):
                existing.custom_labels = json.dumps(custom_labels)
                existing.confidence = confidence.value if confidence else None
                existing.source = source.value if source else None
            # Always refresh metadata.
            existing.sender_name = sender_name
            existing.sender_domain = domain
            existing.email_count = email_count
            existing.sample_subjects = json.dumps(sample_subjects)
            existing.classified_at = now
        else:
            db.add(
                SenderClassification(
                    account_id=account_id,
                    sender_email=sender_email,
                    sender_domain=domain,
                    sender_name=sender_name,
                    custom_labels=json.dumps(custom_labels),
                    sample_subjects=json.dumps(sample_subjects),
                    email_count=email_count,
                    confidence=confidence.value if confidence else None,
                    source=source.value if source else None,
                    classified_at=now,
                )
            )

    db.commit()

    return {
        "total_senders": total,
        "classified": classified,
        "unclassified": unclassified,
    }


def manual_classify(
    account_id: int,
    sender_email: str,
    custom_labels: list[str],
    db: Session,
) -> SenderClassification:
    """
    Apply a user-supplied label list to a sender. Always wins over rule/AI.
    """
    validated = [l for l in custom_labels if l in CUSTOM_LABELS][:3]
    now = datetime.utcnow()

    existing = db.execute(
        select(SenderClassification).where(
            SenderClassification.account_id == account_id,
            SenderClassification.sender_email == sender_email,
        )
    ).scalar_one_or_none()

    if existing:
        existing.custom_labels = json.dumps(validated)
        existing.confidence = ClassificationConfidence.high.value
        existing.source = ClassificationSource.manual.value
        existing.classified_at = now
        db.commit()
        return existing

    domain = sender_email.split("@")[1].lower() if "@" in sender_email else ""
    sc = SenderClassification(
        account_id=account_id,
        sender_email=sender_email,
        sender_domain=domain,
        custom_labels=json.dumps(validated),
        sample_subjects="[]",
        email_count=0,
        confidence=ClassificationConfidence.high.value,
        source=ClassificationSource.manual.value,
        classified_at=now,
    )
    db.add(sc)
    db.commit()
    return sc
