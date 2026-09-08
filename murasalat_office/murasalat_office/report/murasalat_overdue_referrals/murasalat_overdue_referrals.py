"""Operational overdue referral report, always constrained by correspondence visibility."""
from __future__ import annotations
import frappe
from murasalat_office.security.permissions import get_permission_query_conditions

OPEN = ("Pending", "Sent", "Received", "In Progress", "Overdue")

def execute(filters=None):
    filters = frappe._dict(filters or {})
    user = filters.get("user") or frappe.session.user
    where = ["r.status IN %(open)s", "r.due_date IS NOT NULL", "r.due_date < CURDATE()"]
    values = {"open": OPEN}
    condition = get_permission_query_conditions(user)
    if condition:
        where.append(condition.replace("`tabMurasalat Correspondence`", "c"))
    if filters.get("organization"):
        where.append("r.recipient_organization=%(organization)s")
        values["organization"] = filters.organization
    if filters.get("user_filter"):
        where.append("r.recipient_user=%(user_filter)s")
        values["user_filter"] = filters.user_filter
    if filters.get("from_date"):
        where.append("r.due_date >= %(from_date)s")
        values["from_date"] = filters.from_date
    data = frappe.db.sql(f"""
        SELECT c.name, c.subject, c.correspondence_type, c.confidentiality,
               r.name AS referral_id, r.referral_number, r.recipient_type,
               r.recipient_organization, r.recipient_user, r.direction,
               r.status AS referral_status, r.due_date, r.importance,
               DATEDIFF(CURDATE(), r.due_date) AS overdue_days, r.instructions
        FROM `tabMurasalat Correspondence` c
        INNER JOIN `tabMurasalat Referral` r ON r.parent=c.name
          AND r.parenttype='Murasalat Correspondence'
        WHERE {' AND '.join(where)}
        ORDER BY overdue_days DESC, r.due_date ASC, c.modified DESC
    """, values, as_dict=True)
    columns = [
        {"label":"Overdue Days","fieldname":"overdue_days","fieldtype":"Int","width":110},
        {"label":"Correspondence","fieldname":"name","fieldtype":"Link","options":"Murasalat Correspondence","width":180},
        {"label":"Subject","fieldname":"subject","fieldtype":"Data","width":260},
        {"label":"Referral","fieldname":"referral_number","fieldtype":"Data","width":120},
        {"label":"Recipient Organization","fieldname":"recipient_organization","fieldtype":"Link","options":"Murasalat Organization Entity","width":180},
        {"label":"Recipient User","fieldname":"recipient_user","fieldtype":"Link","options":"User","width":180},
        {"label":"Direction","fieldname":"direction","fieldtype":"Link","options":"Murasalat Referral Direction","width":160},
        {"label":"Importance","fieldname":"importance","fieldtype":"Link","options":"Murasalat Importance Level","width":130},
        {"label":"Due Date","fieldname":"due_date","fieldtype":"Date","width":110},
        {"label":"Instructions","fieldname":"instructions","fieldtype":"Small Text","width":260},
    ]
    summary = [
        {"value": len(data), "label":"Overdue Referrals", "datatype":"Int", "indicator":"Red"},
        {"value": max([d.overdue_days or 0 for d in data], default=0), "label":"Maximum Days Late", "datatype":"Int", "indicator":"Orange"},
    ]
    return columns, data, None, summary
