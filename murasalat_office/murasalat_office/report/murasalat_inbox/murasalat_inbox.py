"""Permission-aware referral inbox using native Frappe visibility and Workflow state."""

import frappe
from frappe.utils import getdate, today

from murasalat_office.reporting import permission_condition


def execute(filters=None):
    filters = frappe._dict(filters or {})
    user = frappe.session.user
    scope = filters.get("scope") or "My Work"
    due_only = filters.get("due_only")
    workflow_state = filters.get("workflow_state")

    columns = _columns()
    where, values = _build_conditions(user, scope, workflow_state, due_only)
    data = frappe.db.sql(
        f"""
        SELECT
            c.name,
            c.subject,
            c.correspondence_type,
            c.workflow_state AS correspondence_status,
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
            r.workflow_state AS referral_workflow_state,
            r.due_date,
            r.instructions,
            r.follow_up,
            r.received_on,
            r.completed_on
        FROM `tabMurasalat Correspondence` c
        INNER JOIN `tabMurasalat Referral` r ON r.correspondence = c.name
        WHERE {where}
        ORDER BY
            CASE WHEN r.due_date IS NOT NULL AND r.due_date < CURDATE() THEN 0 ELSE 1 END,
            CASE WHEN r.due_date IS NULL THEN 1 ELSE 0 END,
            r.due_date ASC,
            c.modified DESC
        """,
        values,
        as_dict=True,
    )

    for row in data:
        row["attention"] = _attention(row)
        row["is_overdue"] = 1 if row.due_date and getdate(row.due_date) < getdate(today()) else 0

    return columns, data, None, _summary(data)


def _columns():
    return [
        {"label": "Attention", "fieldname": "attention", "fieldtype": "Data", "width": 130},
        {"label": "Correspondence", "fieldname": "name", "fieldtype": "Link", "options": "Murasalat Correspondence", "width": 170},
        {"label": "Subject", "fieldname": "subject", "fieldtype": "Data", "width": 260},
        {"label": "Referral", "fieldname": "referral_number", "fieldtype": "Data", "width": 120},
        {"label": "Direction", "fieldname": "direction", "fieldtype": "Link", "options": "Murasalat Referral Direction", "width": 150},
        {"label": "Workflow State", "fieldname": "referral_workflow_state", "fieldtype": "Data", "width": 160},
        {"label": "Due Date", "fieldname": "due_date", "fieldtype": "Date", "width": 110},
        {"label": "Current Organization", "fieldname": "current_holder", "fieldtype": "Link", "options": "Murasalat Organization Entity", "width": 180},
        {"label": "Current User", "fieldname": "current_holder_user", "fieldtype": "Link", "options": "User", "width": 180},
        {"label": "Instructions", "fieldname": "instructions", "fieldtype": "Small Text", "width": 260},
    ]


def _build_conditions(user, scope, workflow_state, due_only):
    values = {"user": user}
    conditions = ["1=1"]
    parent_condition, parent_values = permission_condition("c", "Murasalat Correspondence")
    referral_condition, referral_values = permission_condition("r", "Murasalat Referral")
    conditions.extend([parent_condition, referral_condition])
    values.update(parent_values)
    values.update(referral_values)

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
            "AND d.enabled=1 AND d.from_date <= CURDATE() AND d.to_date >= CURDATE())"
        )
    elif scope != "All Visible":
        frappe.throw(f"Unknown inbox scope: {scope}")

    if workflow_state:
        conditions.append("r.workflow_state=%(workflow_state)s")
        values["workflow_state"] = workflow_state
    if due_only:
        conditions.append("r.due_date IS NOT NULL AND r.due_date <= CURDATE()")

    return " AND ".join(conditions), values


def _attention(row):
    if row.due_date and getdate(row.due_date) < getdate(today()):
        return "Overdue"
    if row.due_date and getdate(row.due_date) == getdate(today()):
        return "Due Today"
    return row.referral_workflow_state or "Unassigned Workflow State"


def _summary(data):
    total = len(data)
    overdue = sum(1 for d in data if d.is_overdue)
    due_today = sum(1 for d in data if d.attention == "Due Today")
    return [
        {"value": total, "label": "Visible Referrals", "datatype": "Int"},
        {"value": overdue, "label": "Overdue by Due Date", "datatype": "Int", "indicator": "Red"},
        {"value": due_today, "label": "Due Today", "datatype": "Int", "indicator": "Orange"},
    ]
