import frappe
from frappe import _
from frappe.utils import getdate, today

from murasalat_office.services.reporting import enrich_with_correspondence
from murasalat_office.services.lifecycle import OPEN_REFERRAL_FILTERS


def execute(filters=None):
    filters = frappe._dict(filters or {})

    report_filters = [
        *OPEN_REFERRAL_FILTERS,
        ["due_date", "is", "set"],
        ["due_date", "<", today()],
    ]

    department = filters.get("organization") or filters.get("department") or filters.get("Department")
    user = filters.get("user_filter") or filters.get("user")

    if department:
        report_filters.append(
            ["recipient_department", "=", department]
        )

    if user:
        report_filters.append(
            ["recipient_user", "=", user]
        )

    if filters.get("from_date"):
        report_filters.append(
            ["due_date", ">=", filters.from_date]
        )

    query = frappe.qb.get_query(
        "Murasalat Referral",
        fields=[
            "correspondence",
            "name as referral_id",
            "referral_number",
            "recipient_type",
            "recipient_department",
            "recipient_user",
            "direction",
            "workflow_state as referral_workflow_state",
            "due_date",
            "importance",
            "instructions",
        ],
        filters=report_filters,
        ignore_permissions=False,
        order_by="due_date asc, modified desc",
    )

    data = query.run(as_dict=True)

    data = enrich_with_correspondence(
        data,
        [
            "subject",
            "correspondence_direction",
            "confidentiality",
        ],
    )

    for row in data:
        row["overdue_days"] = (
            getdate(today()) - getdate(row.due_date)
        ).days

    data.sort(
        key=lambda row: (
            -row["overdue_days"],
            getdate(row.due_date),
        )
    )

    columns = [
        {
            "label": _("Overdue Days"),
            "fieldname": "overdue_days",
            "fieldtype": "Int",
            "width": 110,
        },
        {
            "label": _("Correspondence"),
            "fieldname": "correspondence",
            "fieldtype": "Link",
            "options": "Murasalat Correspondence",
            "width": 180,
        },
        {
            "label": _("Subject"),
            "fieldname": "subject",
            "fieldtype": "Data",
            "width": 260,
        },
        {
            "label": _("Referral"),
            "fieldname": "referral_number",
            "fieldtype": "Data",
            "width": 120,
        },
        {
            "label": _("Recipient Type"),
            "fieldname": "recipient_type",
            "fieldtype": "Data",
            "width": 130,
        },
        {
            "label": _("Recipient Department"),
            "fieldname": "recipient_department",
            "fieldtype": "Link",
            "options": "Department",
            "width": 180,
        },
        {
            "label": _("Recipient User"),
            "fieldname": "recipient_user",
            "fieldtype": "Link",
            "options": "User",
            "width": 180,
        },
        {
            "label": _("Direction"),
            "fieldname": "direction",
            "fieldtype": "Link",
            "options": "Murasalat Referral Direction",
            "width": 160,
        },
        {
            "label": _("Importance"),
            "fieldname": "importance",
            "fieldtype": "Link",
            "options": "Murasalat Importance Level",
            "width": 130,
        },
        {
            "label": _("Due Date"),
            "fieldname": "due_date",
            "fieldtype": "Date",
            "width": 110,
        },
        {
            "label": _("Instructions"),
            "fieldname": "instructions",
            "fieldtype": "Small Text",
            "width": 260,
        },
    ]

    summary = [
        {
            "value": len(data),
            "label": _("Open Overdue Referrals"),
            "datatype": "Int",
            "indicator": "Red",
        },
        {
            "value": max(
                [d["overdue_days"] for d in data],
                default=0,
            ),
            "label": _("Maximum Days Late"),
            "datatype": "Int",
            "indicator": "Orange",
        },
    ]

    return columns, data, None, summary