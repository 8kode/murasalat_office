"""ملخص الإدارة — the office's own numbers for a period, in one table.

Answers the question no per-record report answers: **how did the office perform this month?**
Every direction is a row, so a general manager compares incoming against outgoing and internal
without opening a single record, and the last row totals them.

Filters: a date range (*from_date*, *to_date*), defaulting to this month so far.
"""
import frappe
from frappe import _

from murasalat_office.services.aging import summary_item
from murasalat_office.services.management import (
    CORRESPONDENCE,
    average,
    days_between,
    direction_label,
    org_options,
    period,
    rows,
)

def _number_column(label, fieldname, width=110):
    return {"label": _(label), "fieldname": fieldname, "fieldtype": "Int", "width": width}


def _float_column(label, fieldname, width=130):
    return {"label": _(label), "fieldname": fieldname, "fieldtype": "Float", "width": width, "precision": 1}


FIELDS = ["name", "correspondence_direction", "creation", "registered_on", "closed_on",
          "record_sealed_on", "due_date", "current_holder"]


def _bucket():
    """One fresh accumulator per direction."""
    return {"received": 0, "registered": 0, "closed": 0, "sealed": 0,
            "open_now": 0, "overdue_open": 0, "close_days": []}


def execute(filters=None):
    filters = frappe._dict(filters or {})
    from_date, to_date = period(filters)
    today = frappe.utils.getdate(frappe.utils.today())

    organizations = org_options(filters.get("organization_doctype") or "Department")
    if filters.get("organization"):
        organizations = {filters["organization"]}

    records = rows(CORRESPONDENCE, FIELDS)
    if filters.get("organization"):
        records = [r for r in records if r.current_holder == filters["organization"]]

    buckets = {direction: _bucket() for direction in ("Incoming", "Outgoing", "Internal")}
    other = _bucket()

    for record in records:
        bucket = buckets.get(record.correspondence_direction, other)
        created = frappe.utils.getdate(record.creation)
        registered = record.registered_on and frappe.utils.getdate(record.registered_on)
        closed = record.closed_on and frappe.utils.getdate(record.closed_on)
        sealed = record.record_sealed_on and frappe.utils.getdate(record.record_sealed_on)

        if from_date <= created <= to_date:
            bucket["received"] += 1
        if registered and from_date <= registered <= to_date:
            bucket["registered"] += 1
        if closed and from_date <= closed <= to_date:
            bucket["closed"] += 1
            bucket["close_days"].append(days_between(record.creation, record.closed_on))
        if sealed and from_date <= sealed <= to_date:
            bucket["sealed"] += 1

        if not closed:
            bucket["open_now"] += 1
            if record.due_date and frappe.utils.getdate(record.due_date) < today:
                bucket["overdue_open"] += 1

    data = []
    totals = _bucket()

    for direction in ("Incoming", "Outgoing", "Internal"):
        bucket = buckets[direction]
        average_close = average(bucket["close_days"])
        data.append({
            "direction": direction_label(direction),
            "received": bucket["received"],
            "registered": bucket["registered"],
            "closed": bucket["closed"],
            "sealed": bucket["sealed"],
            "open_now": bucket["open_now"],
            "overdue_open": bucket["overdue_open"],
            "avg_close_days": average_close,
        })
        for key in ("received", "registered", "closed", "sealed", "open_now", "overdue_open"):
            totals[key] += bucket[key]
        totals["close_days"].extend(bucket["close_days"])

    data.append({
        "direction": _("Total"),
        "received": totals["received"],
        "registered": totals["registered"],
        "closed": totals["closed"],
        "sealed": totals["sealed"],
        "open_now": totals["open_now"],
        "overdue_open": totals["overdue_open"],
        "avg_close_days": average(totals["close_days"]),
    })

    columns = [
        {"label": _("Direction"), "fieldname": "direction", "fieldtype": "Data", "width": 130},
        _number_column("Received", "received"),
        _number_column("Registered", "registered"),
        _number_column("Closed", "closed"),
        _number_column("Sealed", "sealed"),
        _number_column("Open Now", "open_now"),
        _number_column("Overdue", "overdue_open"),
        _float_column("Average Days to Close", "avg_close_days"),
    ]

    closed_total = totals["closed"]
    settled = closed_total / totals["received"] * 100 if totals["received"] else 0

    summary = [
        summary_item(_("Received in Period"), totals["received"]),
        summary_item(_("Closed in Period"), closed_total, indicator="Green" if closed_total else "Gray"),
        summary_item(_("Open Now"), totals["open_now"],
                     indicator="Orange" if totals["open_now"] else "Gray"),
        summary_item(_("Overdue"), totals["overdue_open"],
                     indicator="Red" if totals["overdue_open"] else "Gray"),
        summary_item(_("Average Days to Close"), average(totals["close_days"]), indicator="Blue"),
        summary_item(_("Closed of Received (%)"), round(settled, 1), indicator="Blue"),
    ]

    chart = {
        "data": {
            "labels": [direction_label(d) for d in ("Incoming", "Outgoing", "Internal")],
            "datasets": [
                {"name": _("Received"), "values": [buckets[d]["received"] for d in ("Incoming", "Outgoing", "Internal")]},
                {"name": _("Closed"), "values": [buckets[d]["closed"] for d in ("Incoming", "Outgoing", "Internal")]},
            ],
        },
        "type": "bar",
        "colors": ["#2f6b5f", "#c9821f"],
    }

    return columns, data, _(f"From {from_date} to {to_date}"), chart, summary
