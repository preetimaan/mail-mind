"""
Heuristic email batch analysis (no spaCy / sklearn).
Same dict shape as historical NLPAnalyzer.analyze_batch for stored insights.
"""

from collections import Counter
from typing import Dict, List

from dateutil import tz


def analyze_batch(emails: List[Dict]) -> Dict:
    if not emails:
        return {
            "sender_patterns": {},
            "subject_clusters": [],
            "frequency_analysis": {},
            "categories": {},
            "total_emails": 0,
            "unique_senders": 0,
            "date_range": {"start": None, "end": None},
        }

    subjects = [e.get("subject", "") for e in emails]
    senders = [e.get("sender_email", "") for e in emails]
    dates = [e.get("date_received") for e in emails]

    sender_patterns = _analyze_sender_patterns(emails)
    subject_clusters = _subject_clusters_simple(subjects)
    frequency_analysis = _analyze_frequency(emails, dates)
    categories = _categorize_emails(emails)

    return {
        "sender_patterns": sender_patterns,
        "subject_clusters": subject_clusters,
        "frequency_analysis": frequency_analysis,
        "categories": categories,
        "total_emails": len(emails),
        "unique_senders": len(set(senders)),
        "date_range": _get_date_range(dates),
    }


def _analyze_sender_patterns(emails: List[Dict]) -> Dict:
    sender_counts = Counter(e.get("sender_email", "") for e in emails)
    sender_names = {e.get("sender_email", ""): e.get("sender_name") for e in emails}

    domain_counts = Counter()
    for sender in sender_counts.keys():
        if "@" in sender:
            domain = sender.split("@")[1]
            domain_counts[domain] += sender_counts[sender]

    top_senders = [
        {
            "email": email,
            "name": sender_names.get(email),
            "count": count,
            "percentage": round(count / len(emails) * 100, 2),
        }
        for email, count in sender_counts.most_common(20)
    ]

    return {
        "top_senders": top_senders,
        "top_domains": [
            {"domain": domain, "count": count}
            for domain, count in domain_counts.most_common(10)
        ],
        "total_unique_senders": len(sender_counts),
    }


def _representative_subject(subjects: List[str]) -> str:
    non_empty = [s for s in subjects if s and str(s).strip()]
    if non_empty:
        return min(non_empty, key=len)
    return subjects[0] if subjects else ""


def _subject_clusters_simple(subjects: List[str]) -> List[Dict]:
    if not subjects:
        return []
    unique_subjects = list(dict.fromkeys(subjects))
    sample = unique_subjects[:500]
    return [
        {
            "cluster_id": 0,
            "subjects": sample,
            "count": len(subjects),
            "representative": _representative_subject(unique_subjects),
        }
    ]


def _analyze_frequency(emails: List[Dict], dates: List) -> Dict:
    if not dates:
        return {}
    daily_counts = Counter(d.date() for d in dates if d)
    return {
        "daily_average": round(len(emails) / max(len(daily_counts), 1), 2),
    }


def _categorize_emails(emails: List[Dict]) -> Dict:
    categories = {
        "notifications": 0,
        "newsletters": 0,
        "social": 0,
        "shopping": 0,
        "work": 0,
        "personal": 0,
        "other": 0,
    }

    notification_keywords = [
        "notification",
        "alert",
        "reminder",
        "confirm",
        "receipt",
    ]
    newsletter_keywords = [
        "newsletter",
        "digest",
        "weekly",
        "monthly",
        "unsubscribe",
    ]
    social_keywords = [
        "facebook",
        "twitter",
        "linkedin",
        "instagram",
        "social",
    ]
    shopping_keywords = [
        "order",
        "purchase",
        "shipping",
        "delivery",
        "amazon",
        "ebay",
    ]
    work_keywords = ["meeting", "calendar", "team", "project", "deadline"]

    for email in emails:
        subject = (email.get("subject", "") or "").lower()
        sender = (email.get("sender_email", "") or "").lower()

        categorized = False

        if any(kw in subject for kw in notification_keywords):
            categories["notifications"] += 1
            categorized = True
        elif any(kw in subject or kw in sender for kw in newsletter_keywords):
            categories["newsletters"] += 1
            categorized = True
        elif any(kw in sender for kw in social_keywords):
            categories["social"] += 1
            categorized = True
        elif any(kw in subject or kw in sender for kw in shopping_keywords):
            categories["shopping"] += 1
            categorized = True
        elif any(kw in subject for kw in work_keywords):
            categories["work"] += 1
            categorized = True
        elif "@" in sender and not any(
            kw in sender for kw in ["noreply", "no-reply", "donotreply"]
        ):
            categories["personal"] += 1
            categorized = True

        if not categorized:
            categories["other"] += 1

    return categories


def _get_date_range(dates: List) -> Dict:
    if not dates:
        return {"start": None, "end": None}

    normalized_dates = []
    for date in dates:
        if date is None:
            continue
        if date.tzinfo is not None:
            normalized = date.astimezone(tz.UTC).replace(tzinfo=None)
        else:
            normalized = date
        normalized_dates.append(normalized)

    if not normalized_dates:
        return {"start": None, "end": None}

    return {
        "start": min(normalized_dates).isoformat(),
        "end": max(normalized_dates).isoformat(),
    }
