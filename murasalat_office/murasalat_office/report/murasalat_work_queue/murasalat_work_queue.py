
import frappe
from frappe import _


def execute(filters=None):

    filters = frappe._dict(filters or {})

    conditions = []

    if filters.get("organization"):

        conditions.append(["current_holder", "=", filters.organization])

    if filters.get("user"):

        conditions.append(["current_holder_user", "=", filters.user])

    query = frappe.qb.get_query(

        "Murasalat Correspondence",

        fields=[
            "name",
            "subject",
            "correspondence_direction",
            "workflow_state",
            "current_holder",
            "current_holder_user",
            "due_date",
        ],

        filters=conditions,

        ignore_permissions=False,

        order_by="modified desc",

    )

    columns = [

        {
            "label": _("Correspondence"),
            "fieldname": "name",
            "fieldtype": "Link",
            "options": "Murasalat Correspondence",
            "width": 180,
        },

        {
            "label": _("Subject"),
            "fieldname": "subject",
            "fieldtype": "Data",
            "width": 260,
        },

        {
            "label": _("Type"),
            "fieldname": "correspondence_direction",
            "fieldtype": "Data",
            "width": 100,
        },

        {
            "label": _("Workflow State"),
            "fieldname": "workflow_state",
            "fieldtype": "Data",
            "width": 140,
        },

        {
            "label": _("Department Queue"),
            "fieldname": "current_holder",
            "fieldtype": "Link",
            "options": "Department",
            "width": 180,
        },

        {
            "label": _("User Queue"),
            "fieldname": "current_holder_user",
            "fieldtype": "Link",
            "options": "User",
            "width": 180,
        },

        {
            "label": _("Due Date"),
            "fieldname": "due_date",
            "fieldtype": "Date",
            "width": 100,
        },

    ]

    data = query.run(as_dict=True)

    summary = [

        {
            "value": len(data),
            "label": _("Active Items"),
            "datatype": "Int",
        },

    ]

    return columns, data, None, summary
