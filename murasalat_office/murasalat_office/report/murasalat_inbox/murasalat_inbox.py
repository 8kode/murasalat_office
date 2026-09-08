"""Permission-aware operational inbox for Murasalat.

The inbox intentionally does not duplicate Frappe's Desk/ListView/ToDo. It provides
one operational projection over referrals: what needs my attention now.
"""
from __future__ import annotations

import frappe
from frappe.utils import getdate, today

from murasalat_office.security.permissions import get_permission_query_conditions

OPEN_STATUSES = ("Pending", "Sent", "Received", "In Progress", "Overdue")


def execute(filters=None):
    filters = frappe._dict(filters or {})
    user = filters.get("user") or frappe.session.user
    scope = filters.get("scope") or "My Work"
    due_only = filters.get("due_only")
    status = filters.get("status")

    columns = _columns()
    where, values = _build_conditions(user, scope, status, due_only)
    data = frappe.db.sql(
        f"""
        SELECT
            c.name,
            c.subject,
            c.correspondence_type,
            c.status AS correspondence_status,
            c.confidentiality,
            c.importance,
            c.current_holder,
            c.current_holder_user,
            r.name AS referral_id,
            r.referral_number,
            r.recipient_type,
            r.recipient_organization,
            r.recipient_user,
            r.direction,
            r.status AS referral_status,
            r.due_date,
            r.instructions,
            r.follow_up,
            r.received_on,
            r.completed_on
        FROM `tabMurasalat Correspondence` c
        INNER JOIN `tabMurasalat Referral` r
            ON r.parent = c.name
           AND r.parenttype = 'Murasalat Correspondence'
        WHERE {where}
        ORDER BY
            CASE WHEN r.status='Overdue' THEN 0 ELSE 1 END,
            CASE WHEN r.due_date IS NULL THEN 1 ELSE 0 END,
            r.due_date ASC,
            c.modified DESC
        """,
        values,
        as_dict=True,
    )

    for row in data:
        row["attention"] = _attention(row)
        row["is_overdue"] = 1 if row.referral_status == "Overdue" or (
            row.due_date and getdate(row.due_date) < getdate(today()) and row.referral_status in OPEN_STATUSES
        ) else 0

    return columns, data, None, _summary(data)


def _columns():
    return [
        {"label": "Attention", "fieldname": "attention", "fieldtype": "Data", "width": 130},
        {"label": "Correspondence", "fieldname": "name", "fieldtype": "Link", "options": "Murasalat Correspondence", "width": 170},
        {"label": "Subject", "fieldname": "subject", "fieldtype": "Data", "width": 260},
        {"label": "Referral", "fieldname": "referral_number", "fieldtype": "Data", "width": 120},
        {"label": "Direction", "fieldname": "direction", "fieldtype": "Link", "options": "Murasalat Referral Direction", "width": 150},
        {"label": "Referral Status", "fieldname": "referral_status", "fieldtype": "Data", "width": 130},
        {"label": "Due Date", "fieldname": "due_date", "fieldtype": "Date", "width": 110},
        {"label": "Current Organization", "fieldname": "current_holder", "fieldtype": "Link", "options": "Murasalat Organization Entity", "width": 180},
        {"label": "Current User", "fieldname": "current_holder_user", "fieldtype": "Link", "options": "User", "width": 180},
        {"label": "Instructions", "fieldname": "instructions", "fieldtype": "Small Text", "width": 260},
    ]


def _build_conditions(user, scope, status, due_only):
    values = {"user": user}
    conditions = ["r.status IN %(open_statuses)s"]
    values["open_statuses"] = OPEN_STATUSES

    # Never bypass the document visibility policy in an operational report.
    permission_condition = get_permission_query_conditions(user)
    if permission_condition:
        conditions.append(permission_condition.replace("`tabMurasalat Correspondence`", "c"))

    if scope == "My Work":
        conditions.append("(r.recipient_type='User' AND r.recipient_user=%(user)s)")
    elif scope == "My Organization":
        conditions.append(
            "(r.recipient_type='Organization' AND r.recipient_organization IN "
            "(SELECT organization FROM `tabMurasalat User Organization Membership` "
            "WHERE user=%(user)s AND enabled=1))"
        )
    elif scope == "Delegated to Me":
        conditions.append(
            "EXISTS (SELECT 1 FROM `tabMurasalat Delegation` d "
            "WHERE d.delegator = r.recipient_user AND d.delegate = %(user)s "
            "AND d.enabled=1 AND d.start_date <= CURDATE() AND d.end_date >= CURDATE())"
        )
    elif scope != "All Visible":
        frappe.throw(f"Unknown inbox scope: {scope}")

    if status:
        conditions.append("r.status=%(status)s")
        values["status"] = status
    if due_only:
        conditions.append("r.due_date IS NOT NULL AND r.due_date <= CURDATE()")

    return " AND ".join(conditions), values


def _attention(row):
    if row.referral_status == "Overdue":
        return "Overdue"
    if row.due_date and getdate(row.due_date) < getdate(today()) and row.referral_status in OPEN_STATUSES:
        return "Overdue"
    if row.due_date and getdate(row.due_date) == getdate(today()):
        return "Due Today"
    if row.referral_status in ("Pending", "Sent"):
        return "Pending Receipt"
    if row.referral_status == "Received":
        return "Ready to Start"
    if row.referral_status == "In Progress":
        return "In Progress"
    return row.referral_status


def _summary(data):
    total = len(data)
    overdue = sum(1 for d in data if d.is_overdue)
    due_today = sum(1 for d in data if d.attention == "Due Today")
    pending = sum(1 for d in data if d.attention == "Pending Receipt")
    progress = sum(1 for d in data if d.attention == "In Progress")
    return [
        {"value": total, "label": "Open Inbox", "datatype": "Int"},
        {"value": overdue, "label": "Overdue", "datatype": "Int", "indicator": "Red"},
        {"value": due_today, "label": "Due Today", "datatype": "Int", "indicator": "Orange"},
        {"value": pending, "label": "Pending Receipt", "datatype": "Int", "indicator": "Blue"},
        {"value": progress, "label": "In Progress", "datatype": "Int", "indicator": "Green"},
    ]
