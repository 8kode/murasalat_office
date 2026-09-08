import frappe


def execute(filters=None):
    filters = filters or {}
    columns = [
        {"label":"Correspondence","fieldname":"name","fieldtype":"Link","options":"Murasalat Correspondence","width":180},
        {"label":"Subject","fieldname":"subject","fieldtype":"Data","width":260},
        {"label":"Type","fieldname":"correspondence_type","fieldtype":"Data","width":100},
        {"label":"Status","fieldname":"status","fieldtype":"Data","width":120},
        {"label":"Organization Queue","fieldname":"current_holder","fieldtype":"Link","options":"Murasalat Organization Entity","width":180},
        {"label":"User Queue","fieldname":"current_holder_user","fieldtype":"Link","options":"User","width":180},
        {"label":"Due Date","fieldname":"due_date","fieldtype":"Date","width":100},
    ]
    conditions = []
    values = {}
    if filters.get("organization"):
        conditions.append("current_holder = %(organization)s")
        values["organization"] = filters["organization"]
    if filters.get("user"):
        conditions.append("current_holder_user = %(user)s")
        values["user"] = filters["user"]
    where = (" where " + " and ".join(conditions)) if conditions else ""
    data = frappe.db.sql(f"""
        select name, subject, correspondence_type, status, current_holder, current_holder_user, due_date
        from `tabMurasalat Correspondence`
        {where}
        order by modified desc
    """, values, as_dict=True)
    return columns, data
