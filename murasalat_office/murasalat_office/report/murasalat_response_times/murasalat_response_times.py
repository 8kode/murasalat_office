"""أزمنة الاستجابة — how long each stage of the office's work actually takes.

A general manager asks where the delay is, and an average over the whole cycle cannot answer
it: a file that waits a week to be registered and a day to be answered has a different problem
from one that is registered at once and answered in a month. Each stage is measured on its own.

Filters: date range and, optionally, one direction.
"""
import frappe
from frappe import _

from murasalat_office.services.aging import summary_item
from murasalat_office.services.management import (
    CORRESPONDENCE,
    REFERRAL,
    DIRECTION_LABELS,
    average,
    days_between,
    direction_label,
    period,
    rows,
)

def _number_column(label, fieldname, width=110):
    return {"label": _(label), "fieldname": fieldname, "fieldtype": "Int", "width": width}


def _float_column(label, fieldname, width=130):
    return {"label": _(label), "fieldname": fieldname, "fieldtype": "Float", "width": width, "precision": 1}


STAGES = ("to_register", "referral_send", "send_to_receive", "receive_to_complete", "to_close")

CORRESPONDENCE_FIELDS = ["name", "correspondence_direction", "creation", "registered_on", "closed_on"]
REFERRAL_FIELDS = ["name", "correspondence", "creation", "sent_on", "received_on", "completed_on"]


def _bucket():
    return {stage: [] for stage in STAGES}


def execute(filters=None):
    filters = frappe._dict(filters or {})
    from_date, to_date = period(filters)

    correspondence = rows(CORRESPONDENCE, CORRESPONDENCE_FIELDS)
    direction_of = {record.name: record.correspondence_direction for record in correspondence}

    buckets = {direction: _bucket() for direction in DIRECTION_LABELS}

    for record in correspondence:
        bucket = buckets.get(record.correspondence_direction)
        if bucket is None:
            continue
        bucket["to_register"].append(days_between(record.creation, record.registered_on))
        bucket["to_close"].append(days_between(record.creation, record.closed_on))

    for record in rows(REFERRAL, REFERRAL_FIELDS):
        direction = direction_of.get(record.correspondence)
        bucket = buckets.get(direction)
        if bucket is None:
            continue
        bucket["referral_send"].append(days_between(record.creation, record.sent_on))
        bucket["send_to_receive"].append(days_between(record.sent_on, record.received_on))
        bucket["receive_to_complete"].append(days_between(record.received_on, record.completed_on))

    data = []
    all_stages = _bucket()

    for direction in DIRECTION_LABELS:
        bucket = buckets[direction]
        row = {"direction": direction_label(direction)}
        for stage in STAGES:
            row[stage] = average(bucket[stage])
            row[f"{stage}_n"] = len([v for v in bucket[stage] if v is not None])
            all_stages[stage].extend(bucket[stage])
        data.append(row)

    if filters.get("correspondence_direction"):
        wanted = filters["correspondence_direction"]
        data = [row for row in data if row["direction"] == direction_label(wanted)]

    data.append({"direction": _("Total"), **{stage: average(all_stages[stage]) for stage in STAGES},
                 **{f"{stage}_n": len([v for v in all_stages[stage] if v is not None]) for stage in STAGES}})

    columns = [
        {"label": _("Direction"), "fieldname": "direction", "fieldtype": "Data", "width": 130},
        _float_column("Days to Register", "to_register"),
        _float_column("Days to Send a Referral", "referral_send"),
        _float_column("Days from Send to Receive", "send_to_receive"),
        _float_column("Days from Receive to Complete", "receive_to_complete"),
        _float_column("Days to Close", "to_close"),
        _number_column("Measured", "to_close_n"),
    ]

    slowest = max(
        ((stage, average(all_stages[stage])) for stage in STAGES),
        key=lambda pair: pair[1] or -1,
        default=(None, None),
    )
    slowest_label = {
        "to_register": _("Registration"),
        "referral_send": _("Sending a Referral"),
        "send_to_receive": _("Receipt of a Referral"),
        "receive_to_complete": _("Completing a Referral"),
        "to_close": _("Closing the File"),
    }.get(slowest[0], "-")

    summary = [
        summary_item(_("Average Days to Close"), average(all_stages["to_close"]), indicator="Blue"),
        summary_item(_("Slowest Stage"), slowest_label,
                     indicator="Orange" if slowest[1] else "Gray"),
        summary_item(_("Slowest Stage (days)"), slowest[1], indicator="Orange"),
        summary_item(_("Files Closed (measured)"), len([v for v in all_stages["to_close"] if v is not None]),
                     indicator="Gray"),
    ]

    chart = {
        "data": {
            "labels": [_("Register"), _("Send"), _("Receive"), _("Complete"), _("Close")],
            "datasets": [{
                "name": _("Average Days"),
                "values": [average(all_stages[stage]) or 0 for stage in STAGES],
            }],
        },
        "type": "line",
        "colors": ["#2f6b5f"],
    }

    return columns, data, _(f"From {from_date} to {to_date}"), chart, summary
