"""Referral productivity report using native permission-aware ORM access.

The report intentionally avoids database-specific SQL functions. Frappe's
permission-aware list API supplies only rows visible to the current user;
aggregation is then performed in Python for portable MariaDB/PostgreSQL use.
"""
from collections import defaultdict

import frappe
from frappe.utils import add_days, get_datetime, getdate, today


def execute(filters=None):
    filters = frappe._dict(filters or {})
    conditions = [
        ["recipient_user", "is", "set"],
        ["recipient_user", "!=", ""],
    ]
    if filters.get("from_date"):
        conditions.append(["completed_on", ">=", filters.from_date])
    if filters.get("to_date"):
        conditions.append(["completed_on", "<", add_days(getdate(filters.to_date), 1)])

    fields = [
        "recipient_user",
        "workflow_state",
        "due_date",
        "received_on",
        "completed_on",
        "correspondence",
    ]
    rows = frappe.get_list(
        "Murasalat Referral",
        filters=conditions,
        fields=fields,
        ignore_permissions=False,
        limit_page_length=0,
        order_by="recipient_user asc, workflow_state asc, completed_on asc",
    )

    if filters.get("organization") and rows:
        correspondence_names = list({row.correspondence for row in rows if row.correspondence})
        if correspondence_names:
            visible_correspondence = set(
                frappe.get_list(
                    "Murasalat Correspondence",
                    filters={
                        "name": ["in", correspondence_names],
                        "current_holder": filters.organization,
                    },
                    pluck="name",
                    ignore_permissions=False,
                    limit_page_length=0,
                )
            )
            rows = [row for row in rows if row.correspondence in visible_correspondence]
        else:
            rows = []

    grouped = defaultdict(lambda: {"total": 0, "overdue": 0, "completion_hours": []})
    today_date = getdate(today())
    for row in rows:
        key = (row.recipient_user, row.workflow_state or "")
        item = grouped[key]
        item["total"] += 1
        # Completed work is considered overdue based on when it was actually
        # completed, not whether its due date is merely in the past today.
        if row.due_date and row.completed_on and getdate(row.due_date) < getdate(row.completed_on):
            item["overdue"] += 1
        if row.received_on and row.completed_on:
            hours = (get_datetime(row.completed_on) - get_datetime(row.received_on)).total_seconds() / 3600
            if hours >= 0:
                item["completion_hours"].append(hours)

    data = []
    for (user, workflow_state), item in grouped.items():
        average = (
            sum(item["completion_hours"]) / len(item["completion_hours"])
            if item["completion_hours"]
            else None
        )
        data.append(
            {
                "user": user,
                "workflow_state": workflow_state,
                "total_referrals": item["total"],
                "overdue_by_due_date": item["overdue"],
                "avg_completion_hours": average,
            }
        )

    data.sort(key=lambda row: (row["overdue_by_due_date"], -row["total_referrals"], row["user"], row["workflow_state"]))

    columns = [
        {"label": "User", "fieldname": "user", "fieldtype": "Link", "options": "User", "width": 220},
        {"label": "Workflow State", "fieldname": "workflow_state", "fieldtype": "Data", "width": 180},
        {"label": "Total", "fieldname": "total_referrals", "fieldtype": "Int", "width": 100},
        {"label": "Overdue by Due Date", "fieldname": "overdue_by_due_date", "fieldtype": "Int", "width": 150},
        {"label": "Avg Completion Hours", "fieldname": "avg_completion_hours", "fieldtype": "Float", "width": 160},
    ]
    return columns, data
