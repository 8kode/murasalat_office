import frappe

from murasalat_office.reporting import permission_condition


def execute(filters=None):
    filters = frappe._dict(filters or {})
    columns = [
        {"label": "Correspondence", "fieldname": "name", "fieldtype": "Link", "options": "Murasalat Correspondence", "width": 180},
        {"label": "Subject", "fieldname": "subject", "fieldtype": "Data", "width": 260},
        {"label": "Type", "fieldname": "correspondence_type", "fieldtype": "Data", "width": 100},
        {"label": "Workflow State", "fieldname": "workflow_state", "fieldtype": "Data", "width": 140},
        {"label": "Organization Queue", "fieldname": "current_holder", "fieldtype": "Link", "options": "Murasalat Organization Entity", "width": 180},
        {"label": "User Queue", "fieldname": "current_holder_user", "fieldtype": "Link", "options": "User", "width": 180},
        {"label": "Due Date", "fieldname": "due_date", "fieldtype": "Date", "width": 100},
    ]
    condition, values = permission_condition("c", "Murasalat Correspondence")
    conditions = [condition]
    if filters.get("organization"):
        conditions.append("c.current_holder=%(organization)s")
        values["organization"] = filters.organization
    if filters.get("user"):
        conditions.append("c.current_holder_user=%(user)s")
        values["user"] = filters.user
    where = " WHERE " + " AND ".join(conditions)
    data = frappe.db.sql(
        f"SELECT c.name,c.subject,c.correspondence_type,c.workflow_state,c.current_holder,c.current_holder_user,c.due_date FROM `tabMurasalat Correspondence` c{where} ORDER BY c.modified DESC",
        values,
        as_dict=True,
    )
    return columns, data
