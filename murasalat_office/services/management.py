"""Shared helpers for the management reports.

The three reports answer the questions a general manager and a department head ask, which no
per-record report answers: how much work moved, where it is sitting, and how long it takes.
They share one module so a metric is defined once - ``days_between`` treats a half-finished
pair as "not yet measurable" rather than zero, and ``period`` keeps every report reading the
same two dates the same way.
"""
import frappe
from frappe import _
from frappe.utils import date_diff, get_first_day, getdate

DIRECTION_LABELS = {"Incoming": "وارد", "Outgoing": "صادر", "Internal": "داخلي"}

CORRESPONDENCE = "Murasalat Correspondence"
REFERRAL = "Murasalat Referral"


def period(filters):
    """The two dates every report reads the same way. Empty means this month so far."""
    today = getdate(frappe.utils.today())
    return (
        getdate((filters or {}).get("from_date") or get_first_day(today)),
        getdate((filters or {}).get("to_date") or today),
    )


def days_between(start, end):
    """Whole days from start to end, or None when the pair is not complete yet.

    None is the honest answer for work still in flight, and it is what keeps a report from
    reporting a perfect average made of unfinished items counted as zero.
    """
    if not start or not end:
        return None
    return date_diff(getdate(end), getdate(start))


def average(values):
    """Mean of the values that exist, or None when none do."""
    present = [value for value in values if value is not None]
    if not present:
        return None
    return round(sum(present) / len(present), 1)


def direction_label(value):
    return DIRECTION_LABELS.get(value, value or "")


def rows(doctype, fields, conditions=None, order_by=None):
    """A permission-aware read - the same discipline every report in this app follows."""
    return frappe.get_list(
        doctype,
        filters=conditions or [],
        fields=fields,
        order_by=order_by,
        limit_page_length=0,
        ignore_permissions=False,
    )


def org_options(org_doctype):
    """Every organizational unit that can hold a record, plus any named in the data.

    The DocType may not exist on a framework-only site, so it is probed rather than assumed -
    and a value that appears in the data but not in the master list is still reported.
    """
    names = set()

    try:
        names.update(name for name in frappe.get_all(org_doctype, pluck="name") if name)
    except Exception:
        pass

    return names
