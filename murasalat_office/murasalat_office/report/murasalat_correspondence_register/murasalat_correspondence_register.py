"""سجل المعاملات — the office's register of record.

Answers the question an office manager actually asks: what came in, what went out, what
is still held, and what is sealed. Permission-aware throughout: every read goes through
``frappe.get_list(..., ignore_permissions=False)``, so the register shows only what the
running user may read.

Returns the six-value Script Report contract (columns, data, message, chart,
report_summary) that ``frappe/desk/query_report.py`` unpacks.
"""

import frappe
from frappe import _
from frappe.utils import today

from murasalat_office.services.aging import (
    frappe_chart,
    month_label,
    monthly_volume,
    ordered_months,
    summary_item,
)

DIRECTION_AR = {"Incoming": "وارد", "Outgoing": "صادر", "Internal": "داخلي"}

FIELDS = [
    "name",
    "subject",
    "correspondence_direction",
    "transaction_type",
    "confidentiality",
    "importance",
    "workflow_state",
    "current_holder",
    "external_letter_number",
    "external_letter_date",
    "due_date",
    "page_count",
    "creation",
    "registered_on",
    "closed_on",
    "record_sealed_on",
]


def _conditions(filters):
    conditions = []

    if filters.get("from_date"):
        conditions.append(["creation", ">=", filters.from_date])
    if filters.get("to_date"):
        conditions.append(["creation", "<=", filters.to_date + " 23:59:59"])
    if filters.get("correspondence_direction"):
        conditions.append(["correspondence_direction", "=", filters.correspondence_direction])
    if filters.get("workflow_state"):
        conditions.append(["workflow_state", "=", filters.workflow_state])
    if filters.get("confidentiality"):
        conditions.append(["confidentiality", "=", filters.confidentiality])
    if filters.get("current_holder"):
        conditions.append(["current_holder", "=", filters.current_holder])
    if filters.get("importance"):
        conditions.append(["importance", "=", filters.importance])

    sealing = filters.get("sealing")
    if sealing == "Sealed":
        conditions.append(["record_sealed_on", "is", "set"])
    elif sealing == "Open":
        conditions.append(["record_sealed_on", "is", "not set"])

    return conditions


def _referral_counts(names):
    """Referral tallies per correspondence, batched and permission-aware."""
    counts = {}

    if not names:
        return counts

    rows = frappe.get_list(
        "Murasalat Referral",
        filters={"correspondence": ["in", names]},
        fields=["correspondence", "sent_on", "completed_on"],
        ignore_permissions=False,
        limit_page_length=0,
    )

    for row in rows:
        tally = counts.setdefault(row.correspondence, {"open": 0, "completed": 0, "draft": 0})
        if not row.sent_on:
            tally["draft"] += 1
        elif row.completed_on:
            tally["completed"] += 1
        else:
            tally["open"] += 1

    return counts


def _columns():
    return [
        {"label": _("Correspondence"), "fieldname": "name", "fieldtype": "Link",
         "options": "Murasalat Correspondence", "width": 130},
        {"label": _("Subject"), "fieldname": "subject", "fieldtype": "Data", "width": 280},
        {"label": _("Direction"), "fieldname": "direction_ar", "fieldtype": "Data", "width": 80},
        {"label": _("Transaction Type"), "fieldname": "transaction_type", "fieldtype": "Link",
         "options": "Murasalat Transaction Type", "width": 110},
        {"label": _("Confidentiality"), "fieldname": "confidentiality", "fieldtype": "Link",
         "options": "Murasalat Confidentiality Level", "width": 110},
        {"label": _("Importance"), "fieldname": "importance", "fieldtype": "Link",
         "options": "Murasalat Importance Level", "width": 100},
        {"label": _("State"), "fieldname": "workflow_state", "fieldtype": "Data", "width": 110},
        {"label": _("Current Holder"), "fieldname": "current_holder", "fieldtype": "Link",
         "options": "Department", "width": 160},
        {"label": _("Open Referrals"), "fieldname": "open_referrals", "fieldtype": "Int", "width": 110},
        {"label": _("Draft Referrals"), "fieldname": "draft_referrals", "fieldtype": "Int", "width": 110},
        {"label": _("Completed Referrals"), "fieldname": "completed_referrals", "fieldtype": "Int", "width": 130},
        {"label": _("External No."), "fieldname": "external_letter_number", "fieldtype": "Data", "width": 120},
        {"label": _("External Date"), "fieldname": "external_letter_date", "fieldtype": "Date", "width": 110},
        {"label": _("Due Date"), "fieldname": "due_date", "fieldtype": "Date", "width": 110},
        {"label": _("Pages"), "fieldname": "page_count", "fieldtype": "Int", "width": 70},
        {"label": _("Registered On"), "fieldname": "registered_on", "fieldtype": "Datetime", "width": 150},
        {"label": _("Closed On"), "fieldname": "closed_on", "fieldtype": "Datetime", "width": 150},
        {"label": _("Sealed On"), "fieldname": "record_sealed_on", "fieldtype": "Datetime", "width": 150},
        {"label": _("Created On"), "fieldname": "creation", "fieldtype": "Datetime", "width": 150},
    ]


def execute(filters=None):
    filters = frappe._dict(filters or {})

    rows = frappe.get_list(
        "Murasalat Correspondence",
        filters=_conditions(filters),
        fields=FIELDS,
        ignore_permissions=False,
        limit_page_length=0,
        order_by="creation desc",
    )

    counts = _referral_counts([row.name for row in rows])

    data = []
    for row in rows:
        tally = counts.get(row.name, {})
        data.append(
            {
                "name": row.name,
                "subject": row.subject,
                "direction_ar": DIRECTION_AR.get(
                    row.correspondence_direction, row.correspondence_direction
                ),
                "transaction_type": row.transaction_type,
                "confidentiality": row.confidentiality,
                "importance": row.importance,
                "workflow_state": row.workflow_state,
                "current_holder": row.current_holder,
                "open_referrals": tally.get("open", 0),
                "draft_referrals": tally.get("draft", 0),
                "completed_referrals": tally.get("completed", 0),
                "external_letter_number": row.external_letter_number,
                "external_letter_date": row.external_letter_date,
                "due_date": row.due_date,
                "page_count": row.page_count,
                "registered_on": row.registered_on,
                "closed_on": row.closed_on,
                "record_sealed_on": row.record_sealed_on,
                "creation": row.creation,
            }
        )

    volume = monthly_volume(row.creation for row in rows)
    months = ordered_months(volume)

    chart = frappe_chart(
        [month_label(month) for month in months],
        [volume[month] for month in months],
        _("Correspondence received"),
        "bar",
    )

    direction_counts = {"Incoming": 0, "Outgoing": 0, "Internal": 0}
    for row in rows:
        if row.correspondence_direction in direction_counts:
            direction_counts[row.correspondence_direction] += 1

    sealed = sum(1 for row in rows if row.record_sealed_on)
    closed = sum(1 for row in rows if row.closed_on)
    overdue_due = sum(
        1
        for row in rows
        if row.due_date and not row.closed_on and str(row.due_date) < today()
    )

    summary = [
        summary_item(_("Correspondence"), len(rows)),
        summary_item(_("Incoming"), direction_counts["Incoming"], indicator="Blue"),
        summary_item(_("Outgoing"), direction_counts["Outgoing"], indicator="Blue"),
        summary_item(_("Internal"), direction_counts["Internal"], indicator="Gray"),
        summary_item(_("Sealed"), sealed, indicator="Green"),
        summary_item(_("Closed"), closed, indicator="Gray"),
        summary_item(_("Past Due and Open"), overdue_due, indicator="Red" if overdue_due else "Gray"),
    ]

    return _columns(), data, None, chart, summary
