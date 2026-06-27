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
LABEL_JOB_SEARCH = "Job Search"
LABEL_STUDY = "Study"
LABEL_SOFTWARE = "Software Learning"
LABEL_LIFE_ADMIN = "Life Admin"
LABEL_SHOPPING = "Shopping"
LABEL_SERVICES = "Services"
LABEL_MONEY = "Money"
LABEL_HEALTH = "Health"
LABEL_GOV_TAX = "Gov & Tax"

# ---------------------------------------------------------------------------
# Tier 1 — known sender domain lists (high confidence, single signal enough)
# ---------------------------------------------------------------------------

# Each entry maps a domain suffix to one or more labels.
# Checked via endswith() so subdomains are covered (e.g. mail.linkedin.com).

_TIER1_DOMAINS: list[tuple[tuple[str, ...], list[str]]] = [
    # Career — employment-related (payroll, HR portals for existing employees)
    (
        (
            "adp.com",
            "paychex.com",
            "paylocity.com",
            "gusto.com",
            "bamboohr.com",
            "workday.com",
        ),
        [LABEL_CAREER],
    ),
    # Job Search — recruitment platforms and hiring tools
    (
        (
            "linkedin.com",
            "indeed.com",
            "glassdoor.com",
            "greenhouse.io",
            "lever.co",
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
        [LABEL_JOB_SEARCH],
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
    # Services — consumer platforms, streaming, social, travel, and subscriptions.
    # Intentionally excludes big-tech companies (Google, Apple, Microsoft, Meta, Amazon)
    # that also recruit heavily from the same domain — those are left to tier-2 keywords.
    (
        (
            # Streaming & entertainment
            "netflix.com",
            "spotify.com",
            "hulu.com",
            "disneyplus.com",
            "max.com",
            "hbomax.com",
            "peacocktv.com",
            "paramountplus.com",
            "primevideo.com",
            "pandora.com",
            "soundcloud.com",
            "tidal.com",
            "crunchyroll.com",
            "twitch.tv",
            # Social media (no Meta/Facebook/Instagram — Meta recruits from these)
            "twitter.com",
            "x.com",
            "reddit.com",
            "tiktok.com",
            "snapchat.com",
            "pinterest.com",
            "discord.com",
            "tumblr.com",
            # Real estate & housing browsing
            "zillow.com",
            "redfin.com",
            "trulia.com",
            "realtor.com",
            "apartments.com",
            "zumper.com",
            # Travel & mobility
            "airbnb.com",
            "uber.com",
            "lyft.com",
            "expedia.com",
            "booking.com",
            "hotels.com",
            "kayak.com",
            "vrbo.com",
            "doordash.com",
            "ubereats.com",
            "grubhub.com",
            "instacart.com",
            # Cloud storage
            "dropbox.com",
            "box.com",
            # Gaming
            "steampowered.com",
            "epicgames.com",
            "ea.com",
            "nintendo.com",
            "playstation.com",
            "roblox.com",
            # Publishing & creator platforms
            "medium.com",
            "substack.com",
            "patreon.com",
            # Creative suites
            "adobe.com",
        ),
        [LABEL_SERVICES],
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
    # Life Admin — utilities and property management
    (
        (
            "xfinity.com",
            "att.com",
            "verizon.com",
            "tmobile.com",
            "spectrum.com",
            "cox.com",
            "sce.com",
            "pge.com",
            "coned.com",
            "duke-energy.com",
            "nationalgrid.com",
        ),
        [LABEL_LIFE_ADMIN],
    ),
    # Shopping — carriers and major retailers
    (
        (
            "usps.com",
            "ups.com",
            "fedex.com",
            "dhl.com",
            "uspsdelivers.com",
            "amazon.com",
            "amazon.ca",
            "ebay.com",
            "etsy.com",
            "walmart.com",
            "target.com",
            "bestbuy.com",
            "wayfair.com",
            "overstock.com",
            "newegg.com",
            "costco.com",
            "chewy.com",
            "homedepot.com",
            "lowes.com",
            "nordstrom.com",
            "macys.com",
            "kohls.com",
            "gap.com",
            "oldnavy.com",
            "zara.com",
            "hm.com",
            "asos.com",
            "shein.com",
            "shopify.com",
            "wish.com",
            "aliexpress.com",
        ),
        [LABEL_SHOPPING],
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
            r"\b(payslip|pay stub|paystub|salary slip|earnings statement|"
            r"employment verification|offer accepted|your paycheck|"
            r"annual review|performance review|onboarding)\b",
            re.IGNORECASE,
        ),
        [LABEL_CAREER],
    ),
    (
        re.compile(
            r"\b(interview|offer letter|background check|"
            r"job offer|application received|application status|"
            r"we received your application|your application|"
            r"recruiter|new job|job alert|job opportunity|"
            r"hiring|open position|apply now)\b",
            re.IGNORECASE,
        ),
        [LABEL_JOB_SEARCH],
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
            r"transaction|statement ready|account statement|"
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
    (
        re.compile(
            r"\b(your order|order confirmation|order shipped|"
            r"order delivered|order has been|out for delivery|"
            r"tracking number|your shipment|your package|"
            r"package arrived|package delivered|delivery notification|"
            r"item sold|return label|shopping cart|wishlist)\b",
            re.IGNORECASE,
        ),
        [LABEL_SHOPPING],
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

        # --- Determine auto-classification result for this sender ---
        auto_labels: list[str] = []
        auto_confidence: ClassificationConfidence | None = None
        auto_source: ClassificationSource | None = None

        tier1 = _tier1_labels(domain)
        if tier1:
            auto_labels = tier1[:3]
            auto_confidence = ClassificationConfidence.high
            auto_source = ClassificationSource.tier1_domain
        elif sample_subjects:
            tier2 = _tier2_labels_from_subjects(sample_subjects)
            if tier2:
                auto_labels = tier2[:3]
                auto_confidence = ClassificationConfidence.medium
                auto_source = ClassificationSource.tier2_keyword

        # --- Upsert with per-label source tracking ---
        existing = db.execute(
            select(SenderClassification).where(
                SenderClassification.account_id == account_id,
                SenderClassification.sender_email == sender_email,
            )
        ).scalar_one_or_none()

        if existing:
            existing_label_sources: dict[str, str] = json.loads(
                getattr(existing, "label_sources", None) or "{}"
            )
            existing_labels: list[str] = json.loads(existing.custom_labels or "[]")

            # One-time migration: if label_sources is empty but labels exist,
            # treat all existing labels as manually assigned.
            if not existing_label_sources and existing_labels:
                existing_label_sources = {
                    label: ClassificationSource.manual.value for label in existing_labels
                }

            # Build new per-label sources:
            # 1. Preserve all manually-assigned labels.
            new_label_sources: dict[str, str] = {
                label: src
                for label, src in existing_label_sources.items()
                if src == ClassificationSource.manual.value
            }
            # 2. Apply auto results — promotes manual→auto when engine agrees,
            #    and adds newly detected labels as auto.
            if auto_labels and auto_source:
                for label in auto_labels:
                    new_label_sources[label] = auto_source.value

            # 3. Cap at 3 labels; manual labels take priority over auto.
            if len(new_label_sources) > 3:
                manual_items = [(k, v) for k, v in new_label_sources.items() if v == ClassificationSource.manual.value]
                auto_items = [(k, v) for k, v in new_label_sources.items() if v != ClassificationSource.manual.value]
                new_label_sources = dict((manual_items + auto_items)[:3])

            final_labels = list(new_label_sources.keys())

            # Row-level source/confidence (summary; per-label detail is in label_sources).
            sources_set = set(new_label_sources.values())
            if auto_source and auto_source.value in sources_set:
                row_source: ClassificationSource | None = auto_source
                row_confidence: ClassificationConfidence | None = auto_confidence
            elif sources_set:
                row_source = ClassificationSource.manual
                row_confidence = ClassificationConfidence.high
            else:
                row_source = None
                row_confidence = None

            existing.custom_labels = json.dumps(final_labels)
            existing.label_sources = json.dumps(new_label_sources)
            existing.confidence = row_confidence.value if row_confidence else None
            existing.source = row_source.value if row_source else None
            existing.sender_name = sender_name
            existing.sender_domain = domain
            existing.email_count = email_count
            existing.sample_subjects = json.dumps(sample_subjects)
            existing.classified_at = now
        else:
            new_label_sources = (
                {label: auto_source.value for label in auto_labels} if auto_source else {}
            )
            final_labels = list(new_label_sources.keys())
            db.add(
                SenderClassification(
                    account_id=account_id,
                    sender_email=sender_email,
                    sender_domain=domain,
                    sender_name=sender_name,
                    custom_labels=json.dumps(final_labels),
                    label_sources=json.dumps(new_label_sources),
                    sample_subjects=json.dumps(sample_subjects),
                    email_count=email_count,
                    confidence=auto_confidence.value if auto_confidence else None,
                    source=auto_source.value if auto_source else None,
                    classified_at=now,
                )
            )

        if final_labels:
            classified += 1
        else:
            unclassified += 1

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

    new_label_sources = {label: ClassificationSource.manual.value for label in validated}

    if existing:
        existing.custom_labels = json.dumps(validated)
        existing.label_sources = json.dumps(new_label_sources)
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
        label_sources=json.dumps(new_label_sources),
        sample_subjects="[]",
        email_count=0,
        confidence=ClassificationConfidence.high.value,
        source=ClassificationSource.manual.value,
        classified_at=now,
    )
    db.add(sc)
    db.commit()
    return sc
