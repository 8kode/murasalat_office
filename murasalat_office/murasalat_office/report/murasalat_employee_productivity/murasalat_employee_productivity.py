"""Referral productivity projection grouped by native Workflow state."""
import frappe
from murasalat_office.reporting import permission_condition


def execute(filters=None):
    filters = frappe._dict(filters or {})
    where = ["r.recipient_user IS NOT NULL", "r.recipient_user != ''"]
    values = {}
    parent_condition, native_values = permission_condition("c", "Murasalat Correspondence")
    referral_condition, referral_values = permission_condition("r", "Murasalat Referral")
    where.extend([parent_condition, referral_condition])
    values.update(native_values)
    values.update(referral_values)
    if filters.get("organization"):
        where.append("c.current_holder=%(organization)s")
        values["organization"] = filters.organization
    if filters.get("from_date"):
        where.append("DATE(r.completed_on) >= %(from_date)s")
        values["from_date"] = filters.from_date
    if filters.get("to_date"):
        where.append("DATE(r.completed_on) <= %(to_date)s")
        values["to_date"] = filters.to_date
    data = frappe.db.sql(f"""
      SELECT r.recipient_user AS user,
             COALESCE(r.workflow_state, '') AS workflow_state,
             COUNT(*) AS total_referrals,
             SUM(r.due_date IS NOT NULL AND r.due_date < CURDATE()) AS overdue_by_due_date,
             AVG(CASE WHEN r.completed_on IS NOT NULL AND r.received_on IS NOT NULL
                 THEN TIMESTAMPDIFF(HOUR, r.received_on, r.completed_on) END) AS avg_completion_hours
      FROM `tabMurasalat Referral` r
      INNER JOIN `tabMurasalat Correspondence` c ON c.name=r.correspondence
      WHERE {' AND '.join(where)}
      GROUP BY r.recipient_user, r.workflow_state
      ORDER BY overdue_by_due_date ASC, total_referrals DESC
    """, values, as_dict=True)
    columns = [
      {"label":"User","fieldname":"user","fieldtype":"Link","options":"User","width":220},
      {"label":"Workflow State","fieldname":"workflow_state","fieldtype":"Data","width":180},
      {"label":"Total","fieldname":"total_referrals","fieldtype":"Int","width":100},
      {"label":"Overdue by Due Date","fieldname":"overdue_by_due_date","fieldtype":"Int","width":150},
      {"label":"Avg Completion Hours","fieldname":"avg_completion_hours","fieldtype":"Float","width":160},
    ]
    return columns, data
