import frappe
from frappe import _
from frappe.utils import getdate, today

from murasalat_office.services.lifecycle import OPEN_REFERRAL_FILTERS


def execute(filters=None):
    """Open referral work queue.

    This report intentionally operates on Murasalat Referral rather than
    Correspondence.current_holder_user.

    Department work:
        recipient_type = Department
        recipient_department = selected department

    User work:
        recipient_type = User
        recipient_user = selected user

    Frappe's native permission-aware query remains the visibility boundary.
    """
    filters = frappe._dict(filters or {})

    referral_filters = list(OPEN_REFERRAL_FILTERS)

    if filters.get("organization"):
        referral_filters.append(
            ["recipient_type", "=", "Department"]
        )
        referral_filters.append(
            ["recipient_department", "=", filters.organization]
        )

    if filters.get("user"):
        if filters.get("organization"):
            frappe.throw(_("Choose either Department or User, not both."))
        referral_filters.append(
            ["recipient_type", "=", "User"]
        )
        referral_filters.append(
            ["recipient_user", "=", filters.user]
        )

    query = frappe.qb.get_query(
        "Murasalat Referral",
        fields=[
            "name",
            "referral_number",
            "correspondence",
            "recipient_type",
            "recipient_department",
            "recipient_user",
            "direction",
            "workflow_state",
            "due_date",
            "importance",
            "follow_up",
            "received_on",
        ],
        filters=referral_filters,
        ignore_permissions=False,
        order_by="due_date asc, modified desc",
    )

    data = query.run(as_dict=True)

    correspondence_names = sorted(
        {
            row.correspondence
            for row in data
            if row.correspondence
        }
    )

    correspondence_map = {}

    if correspondence_names:
        rows = frappe.get_list(
            "Murasalat Correspondence",
            filters={
                "name": ["in", correspondence_names],
            },
            fields=[
                "name",
                "subject",
                "correspondence_direction",
                "current_holder",
            ],
            ignore_permissions=False,
            limit_page_length=0,
        )

        correspondence_map = {
            row.name: row
            for row in rows
        }

    today_date = getdate(today())

    for row in data:
        linked = correspondence_map.get(row.correspondence)

        if linked:
            row.subject = linked.subject
            row.correspondence_direction = (
                linked.correspondence_direction
            )
            row.current_holder = linked.current_holder
        else:
            row.subject = "[Restricted]"
            row.correspondence_direction = None
            row.current_holder = None

        if not row.due_date:
            row.attention = _("No Due Date")
        elif getdate(row.due_date) < today_date:
            row.attention = _("Overdue")
        elif getdate(row.due_date) == today_date:
            row.attention = _("Due Today")
        else:
            row.attention = _("Scheduled")

    columns = [
        {
            "label": _("Attention"),
            "fieldname": "attention",
            "fieldtype": "Data",
            "width": 120,
        },
        {
            "label": _("Referral"),
            "fieldname": "referral_number",
            "fieldtype": "Data",
            "width": 130,
        },
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
            "width": 260,
        },
        {
            "label": _("Recipient Type"),
            "fieldname": "recipient_type",
            "fieldtype": "Data",
            "width": 130,
        },
        {
            "label": _("Department"),
            "fieldname": "recipient_department",
            "fieldtype": "Link",
            "options": "Department",
            "width": 180,
        },
        {
            "label": _("User"),
            "fieldname": "recipient_user",
            "fieldtype": "Link",
            "options": "User",
            "width": 200,
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
            "width": 150,
        },
        {
            "label": _("Due Date"),
            "fieldname": "due_date",
            "fieldtype": "Date",
            "width": 110,
        },
        {
            "label": _("Importance"),
            "fieldname": "importance",
            "fieldtype": "Link",
            "options": "Murasalat Importance Level",
            "width": 130,
        },
        {
            "label": _("Follow-up"),
            "fieldname": "follow_up",
            "fieldtype": "Check",
            "width": 90,
        },
        {
            "label": _("Current Department"),
            "fieldname": "current_holder",
            "fieldtype": "Link",
            "options": "Department",
            "width": 180,
        },
    ]

    summary = [
        {
            "value": len(data),
            "label": _("Open Referral Work"),
            "datatype": "Int",
        },
        {
            "value": sum(
                1
                for row in data
                if row.due_date
                and getdate(row.due_date) < today_date
            ),
            "label": _("Overdue"),
            "datatype": "Int",
            "indicator": "Red",
        },
        {
            "value": sum(
                1
                for row in data
                if row.due_date
                and getdate(row.due_date) == today_date
            ),
            "label": _("Due Today"),
            "datatype": "Int",
            "indicator": "Orange",
        },
    ]

    return columns, data, None, None, summary