import frappe
from frappe.utils import getdate, today

from murasalat_office.services.reporting import enrich_with_correspondence


def execute(filters=None):
    filters = frappe._dict(filters or {})
    report_filters = [
        ["due_date", "is", "set"],
        ["due_date", "<", today()],
    ]
    if filters.get("organization"):
        report_filters.append(["recipient_organization", "=", filters.organization])
    if filters.get("user_filter"):
        report_filters.append(["recipient_user", "=", filters.user_filter])
    if filters.get("from_date"):
        report_filters.append(["due_date", ">=", filters.from_date])

    query = frappe.qb.get_query(
        "Murasalat Referral",
        fields=[
            "correspondence",
            "name as referral_id",
            "referral_number",
            "recipient_type",
            "recipient_organization",
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
    data = enrich_with_correspondence(data, ["subject", "correspondence_type", "confidentiality"])
    for row in data:
        row["overdue_days"] = (getdate(today()) - getdate(row.due_date)).days
    data.sort(key=lambda row: (-row["overdue_days"], getdate(row.due_date)))
    columns = [
        {"label": "Overdue Days", "fieldname": "overdue_days", "fieldtype": "Int", "width": 110},
        {"label": "Correspondence", "fieldname": "correspondence", "fieldtype": "Link", "options": "Murasalat Correspondence", "width": 180},
        {"label": "Subject", "fieldname": "subject", "fieldtype": "Data", "width": 260},
        {"label": "Referral", "fieldname": "referral_number", "fieldtype": "Data", "width": 120},
        {"label": "Workflow State", "fieldname": "referral_workflow_state", "fieldtype": "Data", "width": 160},
        {"label": "Recipient Organization", "fieldname": "recipient_organization", "fieldtype": "Link", "options": "Murasalat Organization Entity", "width": 180},
        {"label": "Recipient User", "fieldname": "recipient_user", "fieldtype": "Link", "options": "User", "width": 180},
        {"label": "Direction", "fieldname": "direction", "fieldtype": "Link", "options": "Murasalat Referral Direction", "width": 160},
        {"label": "Importance", "fieldname": "importance", "fieldtype": "Link", "options": "Murasalat Importance Level", "width": 130},
        {"label": "Due Date", "fieldname": "due_date", "fieldtype": "Date", "width": 110},
        {"label": "Instructions", "fieldname": "instructions", "fieldtype": "Small Text", "width": 260},
    ]
    summary = [
        {"value": len(data), "label": "Overdue by Due Date", "datatype": "Int", "indicator": "Red"},
        {"value": max([d["overdue_days"] for d in data], default=0), "label": "Maximum Days Late", "datatype": "Int", "indicator": "Orange"},
    ]
    return columns, data, None, summary
