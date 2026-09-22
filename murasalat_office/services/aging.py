"""Pure age and volume analysis used by the operational reports.

Standard library only, and no Frappe import, so every rule here is unit-testable without
a Bench. The chart and summary builders return the exact shapes the Desk report view
expects — verified against ``frappe/public/js/frappe/views/reports/query_report.js``,
which reads ``data.chart`` as ``{data: {labels, datasets}, type, fieldtype}`` and renders
``report_summary`` entries through ``frappe.utils.build_summary_item``.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date

# Ageing buckets, in reporting order. ``not_due`` means the referral is still within its
# due date; the rest are days late.
AGE_BUCKETS = ("not_due", "0-3", "4-7", "8-14", "15+")

AGE_BUCKET_LABELS = {
    "not_due": "داخل الموعد",
    "0-3": "متأخرة 1-3 أيام",
    "4-7": "متأخرة 4-7 أيام",
    "8-14": "متأخرة 8-14 يومًا",
    "15+": "متأخرة 15 يومًا وأكثر",
}

AGE_BUCKET_COLORS = {
    "not_due": "blue",
    "0-3": "yellow",
    "4-7": "orange",
    "8-14": "red",
    "15+": "red",
}

MONTHS_AR = (
    "يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو",
    "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر",
)

# Frappe chart types accepted by the Desk chart component.
CHART_TYPES = ("bar", "line", "pie", "donut", "percentage")


def to_date(value) -> date | None:
    """Coerce an ORM value (date, datetime or ISO string) to a date."""
    if not value:
        return None
    if isinstance(value, date):
        return value
    text = str(value).strip()
    if not text:
        return None
    return date.fromisoformat(text[:10])


def days_late(due, as_of) -> int | None:
    """Days past the due date. Negative when still inside it, ``None`` without a due date."""
    due_date = to_date(due)
    as_of_date = to_date(as_of)
    if due_date is None or as_of_date is None:
        return None
    return (as_of_date - due_date).days


def aging_bucket(days: int | None) -> str:
    """Bucket a lateness figure. A missing due date is reported as ``not_due``."""
    if days is None or days <= 0:
        return "not_due"
    if days <= 3:
        return "0-3"
    if days <= 7:
        return "4-7"
    if days <= 14:
        return "8-14"
    return "15+"


def month_key(value) -> str | None:
    """Return ``YYYY-MM`` for a date, datetime or ISO string."""
    parsed = to_date(value)
    return f"{parsed.year:04d}-{parsed.month:02d}" if parsed else None


def month_label(key: str) -> str:
    """Render ``YYYY-MM`` as an Arabic month and year for a chart axis."""
    try:
        year, month = key.split("-")
        return f"{MONTHS_AR[int(month) - 1]} {year}"
    except (ValueError, IndexError):
        return key


def ordered_months(keys: Iterable[str]) -> list[str]:
    """Sorted, de-duplicated month keys."""
    return sorted({key for key in keys if key})


def monthly_volume(values: Iterable) -> dict[str, int]:
    """Count values per month, keyed ``YYYY-MM``."""
    volume: dict[str, int] = {}
    for value in values:
        key = month_key(value)
        if key:
            volume[key] = volume.get(key, 0) + 1
    return volume


def summarize_aging(rows: Iterable[dict], as_of) -> dict:
    """Bucket open referrals by lateness and collect the headline figures."""
    counts = {bucket: 0 for bucket in AGE_BUCKETS}
    total = 0
    worst = 0
    without_due_date = 0
    overdue = 0

    for row in rows:
        total += 1
        days = days_late(row.get("due_date"), as_of)

        if days is None:
            without_due_date += 1
            continue

        bucket = aging_bucket(days)
        counts[bucket] += 1

        if days > 0:
            overdue += 1
            worst = max(worst, days)

    return {
        "total_open": total,
        "overdue": overdue,
        "within_due": counts["not_due"],
        "without_due_date": without_due_date,
        "worst_days": worst,
        "buckets": counts,
    }


def frappe_chart(labels: list[str], values: list, label: str, chart_type: str = "bar") -> dict:
    """Build the chart dict the Desk report view renders.

    ``query_report.js`` reads ``chart.data.labels`` and renders nothing when the list is
    empty, so an empty series is returned as ``None`` instead of a blank card.
    """
    if not labels or chart_type not in CHART_TYPES:
        return None

    return {
        "data": {
            "labels": list(labels),
            "datasets": [{"name": label, "values": [int(value or 0) for value in values]}],
        },
        "type": chart_type,
        "fieldtype": "Int",
    }


def summary_item(label: str, value, datatype: str = "Int", indicator: str | None = None) -> dict:
    """Build one ``report_summary`` entry for ``frappe.utils.build_summary_item``."""
    item = {"label": label, "value": value, "datatype": datatype}
    if indicator:
        item["indicator"] = indicator
    return item


def bucket_chart(counts: dict[str, int], chart_type: str = "bar") -> dict:
    """Chart the ageing buckets in reporting order, in Arabic."""
    labels = [AGE_BUCKET_LABELS[bucket] for bucket in AGE_BUCKETS]
    values = [counts.get(bucket, 0) for bucket in AGE_BUCKETS]
    return frappe_chart(labels, values, "الإحالات", chart_type)
