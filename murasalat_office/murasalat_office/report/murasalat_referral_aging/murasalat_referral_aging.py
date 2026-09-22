"""تقادم الإحالات — how late the open work is, and where it is sitting.

Aging is the question a correspondence office cannot answer from a status column: an
open referral that is three days late and one that is forty days late are the same state
and very different problems. This report buckets open referrals by lateness and charts
them.

Permission-aware: rows come from ``frappe.get_list(..., ignore_permissions=False)``.
"""

import frappe
from frappe import _

from murasalat_office.services.aging import (
    AGE_BUCKET_LABELS,
    AGE_BUCKETS,
    aging_bucket,
    bucket_chart,
    days_late,
    summary_item,
)
from murasalat_office.services.lifecycle import OPEN_REFERRAL_FILTERS

FIELDS = [
    "name",
    "referral_number",
    "correspondence",
    "recipient_type",
    "recipient_user",
    "recipient_department",
    "importance",
    "workflow_state",
    "due_date",
    "sent_on",
    "follow_up",
    "private_referral",
]


def _conditions(filters):
    conditions = list(OPEN_REFERRAL_FILTERS)

    if filters.get("organization"):
        conditions.append(["recipient_department", "=", filters.organization])
    if filters.get("user"):
        conditions.append(["recipient_user", "=", filters.user])
    if filters.get("importance"):
        conditions.append(["importance", "=", filters.importance])

    if filters.get("only_overdue"):
        conditions.append(["due_date", "is", "set"])
        conditions.append(["due_date", "<", filters.get("as_of_date") or frappe.utils.today()])

    return conditions


def _columns():
    return [
        {"label": _("Referral"), "fieldname": "referral_number", "fieldtype": "Data", "width": 130},
        {"label": _("Correspondence"), "fieldname": "correspondence", "fieldtype": "Link",
         "options": "Murasalat Correspondence", "width": 130},
        {"label": _("Recipient"), "fieldname": "recipient_label", "fieldtype": "Data", "width": 200},
        {"label": _("Importance"), "fieldname": "importance", "fieldtype": "Link",
         "options": "Murasalat Importance Level", "width": 100},
        {"label": _("State"), "fieldname": "workflow_state", "fieldtype": "Data", "width": 110},
        {"label": _("Due Date"), "fieldname": "due_date", "fieldtype": "Date", "width": 110},
        {"label": _("Days Late"), "fieldname": "days_late", "fieldtype": "Int", "width": 100},
        {"label": _("Age Band"), "fieldname": "bucket_label", "fieldtype": "Data", "width": 170},
        {"label": _("Sent On"), "fieldname": "sent_on", "fieldtype": "Datetime", "width": 150},
        {"label": _("Follow Up"), "fieldname": "follow_up", "fieldtype": "Check", "width": 90},
        {"label": _("Private"), "fieldname": "private_referral", "fieldtype": "Check", "width": 80},
    ]


def execute(filters=None):
    filters = frappe._dict(filters or {})
    as_of = filters.get("as_of_date") or frappe.utils.today()

    rows = frappe.get_list(
        "Murasalat Referral",
        filters=_conditions(filters),
        fields=FIELDS,
        ignore_permissions=False,
        limit_page_length=0,
        order_by="due_date asc, creation asc",
    )

    data = []
    for row in rows:
        days = days_late(row.due_date, as_of)
        bucket = aging_bucket(days)
        data.append(
            {
                "name": row.name,
                "referral_number": row.referral_number or row.name,
                "correspondence": row.correspondence,
                "recipient_label": row.recipient_user or row.recipient_department or "—",
                "importance": row.importance,
                "workflow_state": row.workflow_state,
                "due_date": row.due_date,
                "days_late": days if days is not None else 0,
                "bucket_label": AGE_BUCKET_LABELS[bucket],
                "sent_on": row.sent_on,
                "follow_up": row.follow_up,
                "private_referral": row.private_referral,
            }
        )

    # oldest first, so the report reads as a worklist rather than an index
    data.sort(key=lambda item: item["days_late"], reverse=True)

    counts = {bucket: 0 for bucket in AGE_BUCKETS}
    for item in data:
        counts[aging_bucket(item["days_late"] if item["due_date"] else None)] += 1

    worst = max((item["days_late"] for item in data), default=0)
    overdue = sum(1 for item in data if item["days_late"] > 0)

    summary = [
        summary_item(_("Open Referrals"), len(data)),
        summary_item(_("Overdue"), overdue, indicator="Red" if overdue else "Gray"),
        summary_item(_("Worst Lateness (days)"), worst, indicator="Orange" if worst else "Gray"),
        summary_item(_("15+ Days Late"), counts["15+"], indicator="Red" if counts["15+"] else "Gray"),
        summary_item(_("Within Due Date"), counts["not_due"], indicator="Green"),
        summary_item(_("No Due Date"), sum(1 for item in data if not item["due_date"]), indicator="Gray"),
    ]

    return _columns(), data, None, bucket_chart(counts), summary
