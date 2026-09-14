import frappe
from frappe.utils import getdate, today

from murasalat_office.services.reporting import enrich_with_correspondence


def execute(filters=None):
    """Personal action queue: referrals sent to the current user and not completed.

    Visibility is still enforced by Frappe Query Builder with
    ``ignore_permissions=False``. The report does not implement authorization.
    """
    user = frappe.session.user
    query = frappe.qb.get_query(
        "Murasalat Referral",
        fields=[
            "name",
            "referral_number",
            "correspondence",
            "recipient_type",
            "direction",
            "importance",
            "workflow_state",
            "due_date",
            "follow_up",
            "sent_on",
            "received_on",
            "modified",
        ],
        filters=[
            ["recipient_type", "=", "User"],
            ["recipient_user", "=", user],
            ["sent_on", "is", "set"],
            ["completed_on", "is", "not set"],
        ],
        ignore_permissions=False,
        order_by="due_date asc, modified desc",
    )
    data = query.run(as_dict=True)
    data = enrich_with_correspondence(
        data,
        ["subject", "correspondence_type", "current_holder"],
    )

    today_date = getdate(today())
    for row in data:
        due = getdate(row.due_date) if row.due_date else None
        if not due:
            row["attention"] = "No Due Date"
        elif due < today_date:
            row["attention"] = "Overdue"
        elif due == today_date:
            row["attention"] = "Due Today"
        else:
            row["attention"] = "Scheduled"

    columns = [
        {"label": "Attention", "fieldname": "attention", "fieldtype": "Data", "width": 120},
        {"label": "Referral", "fieldname": "name", "fieldtype": "Link", "options": "Murasalat Referral", "width": 130},
        {"label": "Correspondence", "fieldname": "correspondence", "fieldtype": "Link", "options": "Murasalat Correspondence", "width": 170},
        {"label": "Subject", "fieldname": "subject", "fieldtype": "Data", "width": 280},
        {"label": "Status", "fieldname": "workflow_state", "fieldtype": "Data", "width": 150},
        {"label": "Importance", "fieldname": "importance", "fieldtype": "Link", "options": "Murasalat Importance Level", "width": 120},
        {"label": "Due Date", "fieldname": "due_date", "fieldtype": "Date", "width": 110},
        {"label": "Follow-up", "fieldname": "follow_up", "fieldtype": "Check", "width": 90},
        {"label": "Department", "fieldname": "current_holder", "fieldtype": "Link", "options": "Department", "width": 180},
    ]
    return columns, data