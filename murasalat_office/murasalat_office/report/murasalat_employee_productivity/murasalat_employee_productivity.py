"""Manager productivity projection from immutable referral events, not a parallel KPI store."""
from __future__ import annotations
import frappe

def execute(filters=None):
    filters = frappe._dict(filters or {})
    where = ["r.parenttype='Murasalat Correspondence'", "r.recipient_user IS NOT NULL", "r.recipient_user != ''"]
    values = {}
    if filters.get("organization"):
        where.append("c.current_holder=%(organization)s")
        values["organization"] = filters.organization
    if filters.get("from_date"):
        where.append("DATE(COALESCE(r.completed_on, r.sent_on)) >= %(from_date)s")
        values["from_date"] = filters.from_date
    if filters.get("to_date"):
        where.append("DATE(COALESCE(r.completed_on, r.sent_on)) <= %(to_date)s")
        values["to_date"] = filters.to_date
    data = frappe.db.sql(f"""
      SELECT r.recipient_user AS user,
             COUNT(*) AS total_referrals,
             SUM(r.status IN ('Received','In Progress')) AS active_referrals,
             SUM(r.status='Completed') AS completed_referrals,
             SUM((r.status='Overdue' OR (r.due_date < CURDATE() AND r.status IN ('Pending','Sent','Received','In Progress')))) AS overdue_referrals,
             AVG(CASE WHEN r.completed_on IS NOT NULL AND r.received_on IS NOT NULL
                 THEN TIMESTAMPDIFF(HOUR, r.received_on, r.completed_on) END) AS avg_completion_hours
      FROM `tabMurasalat Referral` r
      INNER JOIN `tabMurasalat Correspondence` c ON c.name=r.parent
      WHERE {' AND '.join(where)}
      GROUP BY r.recipient_user
      ORDER BY overdue_referrals ASC, completed_referrals DESC, total_referrals DESC
    """, values, as_dict=True)
    for row in data:
        row["completion_rate"] = round((row.completed_referrals or 0) * 100 / row.total_referrals, 2) if row.total_referrals else 0
    columns = [
      {"label":"User","fieldname":"user","fieldtype":"Link","options":"User","width":220},
      {"label":"Total","fieldname":"total_referrals","fieldtype":"Int","width":100},
      {"label":"Active","fieldname":"active_referrals","fieldtype":"Int","width":100},
      {"label":"Completed","fieldname":"completed_referrals","fieldtype":"Int","width":110},
      {"label":"Overdue","fieldname":"overdue_referrals","fieldtype":"Int","width":100},
      {"label":"Completion %","fieldname":"completion_rate","fieldtype":"Percent","width":120},
      {"label":"Avg Completion Hours","fieldname":"avg_completion_hours","fieldtype":"Float","width":160},
    ]
    return columns, data
