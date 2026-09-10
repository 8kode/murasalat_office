import frappe

from murasalat_office.services.reporting import enrich_with_correspondence


def execute(filters=None):
    columns = [
        {"label": "Correspondence", "fieldname": "correspondence", "fieldtype": "Link", "options": "Murasalat Correspondence", "width": 180},
        {"label": "Referral", "fieldname": "name", "fieldtype": "Link", "options": "Murasalat Referral", "width": 130},
        {"label": "Subject", "fieldname": "subject", "fieldtype": "Data", "width": 280},
        {"label": "Workflow State", "fieldname": "workflow_state", "fieldtype": "Data", "width": 160},
        {"label": "Direction", "fieldname": "direction", "fieldtype": "Link", "options": "Murasalat Referral Direction", "width": 150},
        {"label": "Due Date", "fieldname": "due_date", "fieldtype": "Date", "width": 110},
        {"label": "Follow Up", "fieldname": "follow_up", "fieldtype": "Check", "width": 90},
    ]
    query = frappe.qb.get_query(
        "Murasalat Referral",
        fields=["correspondence", "name", "workflow_state", "direction", "due_date", "follow_up"],
        filters={"recipient_user": frappe.session.user},
        ignore_permissions=False,
        order_by="due_date asc, modified desc",
    )
    data = query.run(as_dict=True)
    return columns, enrich_with_correspondence(data, ["subject"])
