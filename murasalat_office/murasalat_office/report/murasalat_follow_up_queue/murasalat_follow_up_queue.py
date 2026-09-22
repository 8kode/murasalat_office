import frappe
from frappe import _

from murasalat_office.services.reporting import enrich_with_correspondence
from murasalat_office.services.lifecycle import OPEN_REFERRAL_FILTERS


def execute(filters=None):
    columns = [
        {
            "label": _("Correspondence"),
            "fieldname": "correspondence",
            "fieldtype": "Link",
            "options": "Murasalat Correspondence",
            "width": 180,
        },
        {
            "label": _("Subject"),
            "fieldname": "subject",
            "fieldtype": "Data",
            "width": 280,
        },
        {
            "label": _("Referral"),
            "fieldname": "referral_number",
            "fieldtype": "Data",
            "width": 130,
        },
        {
            "label": _("Recipient Type"),
            "fieldname": "recipient_type",
            "fieldtype": "Data",
            "width": 130,
        },
        {
            "label": _("Recipient Department"),
            "fieldname": "recipient_department",
            "fieldtype": "Link",
            "options": "Department",
            "width": 180,
        },
        {
            "label": _("Recipient User"),
            "fieldname": "recipient_user",
            "fieldtype": "Link",
            "options": "User",
            "width": 180,
        },
        {
            "label": _("Direction"),
            "fieldname": "direction",
            "fieldtype": "Link",
            "options": "Murasalat Referral Direction",
            "width": 150,
        },
        {
            "label": _("Workflow State"),
            "fieldname": "workflow_state",
            "fieldtype": "Data",
            "width": 160,
        },
        {
            "label": _("Due Date"),
            "fieldname": "due_date",
            "fieldtype": "Date",
            "width": 110,
        },
    ]

    query = frappe.qb.get_query(
        "Murasalat Referral",
        fields=[
            "correspondence",
            "name as referral_id",
            "referral_number",
            "recipient_type",
            "recipient_department",
            "recipient_user",
            "direction",
            "workflow_state",
            "due_date",
        ],
        filters=[
            *OPEN_REFERRAL_FILTERS,
            ["follow_up", "=", 1],
        ],
        ignore_permissions=False,
        order_by="due_date asc, modified desc",
    )

    data = query.run(as_dict=True)

    data = enrich_with_correspondence(
        data,
        ["subject"],
    )

    return columns, data