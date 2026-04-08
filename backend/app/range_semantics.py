"""
Processed ranges and batch analysis — **one** time-window contract.

**Half-open interval** ``[start, end)`` (``datetime``, naive project timeline):

- ``start``: **inclusive** — first covered instant (stored/processed as 00:00:00).
- ``end``: **exclusive** — first instant **not** covered (00:00:00 on the calendar
  day after the last covered calendar day).

**Email membership** (metadata ``date_received``)::

    normalize(instant)  # strip tz → naive UTC wall-clock for comparison
    window_start <= instant < window_end

**SQL overlap** between stored row ``(row_start, row_end)`` and window ``(w_start, w_end)``::

    row_start < w_end AND row_end > w_start

Touching rows ``[a, b)`` and ``[b, c)`` do **not** intersect (SQL overlap) but **merge** for gap
display and UI when sorted (see ``merge_touching_or_overlapping_sorted``).

All callers should use these helpers so behavior cannot drift.
"""
from __future__ import annotations

from datetime import datetime, time, timedelta
from typing import List, Tuple

__all__ = [
    "naive_utc_instant",
    "truncate_to_midnight",
    "normalize_analysis_window",
    "is_valid_half_open",
    "half_open_contains_instant",
    "half_open_intersect_non_empty",
    "half_open_row_overlaps_window",
    "merge_sorted_half_open",
    "half_open_sorted_mergeable",
    "merge_touching_or_overlapping_sorted",
    "split_interval_removing_window",
    "reconstruct_bounds_from_email_min_max",
]


def naive_utc_instant(dt: datetime | None) -> datetime | None:
    """Timezone-aware → UTC wall as naive; naive → unchanged."""
    if dt is None:
        return None
    if dt.tzinfo is not None:
        from dateutil import tz as dateutil_tz

        return dt.astimezone(dateutil_tz.UTC).replace(tzinfo=None)
    return dt


def truncate_to_midnight(dt: datetime) -> datetime:
    d = naive_utc_instant(dt)
    return d.replace(hour=0, minute=0, second=0, microsecond=0)


def normalize_analysis_window(start: datetime, end: datetime) -> Tuple[datetime, datetime]:
    """Naive midnights for ``[start, end)`` batch / ProcessedDateRange."""
    return truncate_to_midnight(start), truncate_to_midnight(end)


def is_valid_half_open(start: datetime, end: datetime) -> bool:
    return end > start


def half_open_contains_instant(
    instant: datetime,
    window_start: datetime,
    window_end_exclusive: datetime,
) -> bool:
    t = naive_utc_instant(instant)
    ws = naive_utc_instant(window_start)
    we = naive_utc_instant(window_end_exclusive)
    return ws <= t < we


def half_open_intersect_non_empty(
    a_start: datetime,
    a_end_exclusive: datetime,
    b_start: datetime,
    b_end_exclusive: datetime,
) -> bool:
    """True iff ``[a_start, a_end) ∩ [b_start, b_end)`` is non-empty."""
    return max(a_start, b_start) < min(a_end_exclusive, b_end_exclusive)


def half_open_row_overlaps_window(
    row_start: datetime,
    row_end_exclusive: datetime,
    window_start: datetime,
    window_end_exclusive: datetime,
) -> bool:
    """SQL-aligned overlap (non-empty intersection): ``row_start < win_end AND row_end > win_start``."""
    return row_start < window_end_exclusive and row_end_exclusive > window_start


def merge_sorted_half_open(
    intervals: List[Tuple[datetime, datetime]],
) -> List[Tuple[datetime, datetime]]:
    """
    Merge **sorted** half-open intervals that **overlap** (non-empty intersection only).
    Touching ``[a, b)`` and ``[b, c)`` are **not** merged here.
    """
    if not intervals:
        return []
    out: List[Tuple[datetime, datetime]] = [intervals[0]]
    for s, e in intervals[1:]:
        ps, pe = out[-1]
        if s < pe and ps < e:
            out[-1] = (ps, max(pe, e))
        else:
            out.append((s, e))
    return out


def half_open_sorted_mergeable(
    next_start: datetime,
    prev_end_exclusive: datetime,
) -> bool:
    """After sorting by ``start``, merge into the previous row when this holds (touch or overlap)."""
    return next_start <= prev_end_exclusive


def merge_touching_or_overlapping_sorted(
    intervals: List[Tuple[datetime, datetime]],
) -> List[Tuple[datetime, datetime]]:
    """
    Merge sorted intervals where consecutive intervals **touch or overlap**:
    ``next_start <= prev_end_exclusive`` (same rule as ProcessedDateRange UI merge).
    """
    if not intervals:
        return []
    out: List[Tuple[datetime, datetime]] = [intervals[0]]
    for s, e in intervals[1:]:
        ps, pe = out[-1]
        if half_open_sorted_mergeable(s, pe):
            out[-1] = (ps, max(pe, e))
        else:
            out.append((s, e))
    return out


def split_interval_removing_window(
    r_start: datetime,
    r_end_exclusive: datetime,
    cut_start: datetime,
    cut_end_exclusive: datetime,
) -> List[Tuple[datetime, datetime]]:
    """
    Return the kept pieces of ``[r_start, r_end)`` after removing ``[cut_start, cut_end)``.
    At most two intervals; both half-open.
    """
    kept: List[Tuple[datetime, datetime]] = []
    before_end = min(r_end_exclusive, cut_start)
    if r_start < before_end:
        kept.append((r_start, before_end))
    after_start = max(r_start, cut_end_exclusive)
    if after_start < r_end_exclusive:
        kept.append((after_start, r_end_exclusive))
    return kept


def reconstruct_bounds_from_email_min_max(
    min_date_received: datetime,
    max_date_received: datetime,
) -> Tuple[datetime, datetime]:
    """
    Half-open processed range covering all emails from min→max calendar days:
    ``[min_midnight, day_after_max_calendar_day at midnight)``.
    """
    mn = naive_utc_instant(min_date_received)
    mx = naive_utc_instant(max_date_received)
    start = mn.replace(hour=0, minute=0, second=0, microsecond=0)
    last_calendar_day = mx.date()
    end = datetime.combine(last_calendar_day + timedelta(days=1), time.min)
    return start, end
