"""عبء الأقسام — where the work is sitting, and which department is behind.

A status column cannot answer this: ten open files held by one department and ten spread over
ten departments are the same count and a different problem. One row per organizational unit.

Filters: date range, and optionally one unit.
"""
import frappe
from frappe import _

from murasalat_office.services.aging import summary_item
from murasalat_office.services.management import (
    CORRESPONDENCE,
    REFERRAL,
    average,
    days_between,
    period,
    rows,
)

def _number_column(label, fieldname, width=110):
    return {"label": _(label), "fieldname": fieldname, "fieldtype": "Int", "width": width}


def _float_column(label, fieldname, width=130):
    return {"label": _(label), "fieldname": fieldname, "fieldtype": "Float", "width": width, "precision": 1}


CORRESPONDENCE_FIELDS = ["name", "current_holder", "creation", "closed_on", "due_date"]
REFERRAL_FIELDS = ["name", "recipient_department", "sent_on", "received_on",
                   "completed_on", "due_date", "workflow_state"]


def _unit():
    return {"holding": 0, "open_referrals": 0, "overdue_referrals": 0,
            "completed": 0, "complete_days": [], "oldest_open": 0}


def execute(filters=None):
    filters = frappe._dict(filters or {})
    from_date, to_date = period(filters)
    today = frappe.utils.getdate(frappe.utils.today())

    units = {}

    def bucket(name):
        return units.setdefault(name, _unit())

    for record in rows(CORRESPONDENCE, CORRESPONDENCE_FIELDS):
        if not record.current_holder:
            continue
        item = bucket(record.current_holder)
        if not record.closed_on:
            item["holding"] += 1
            age = days_between(record.creation, today) or 0
            item["oldest_open"] = max(item["oldest_open"], age)

    for record in rows(REFERRAL, REFERRAL_FIELDS):
        unit = record.recipient_department
        if not unit:
            continue
        item = bucket(unit)
        if record.workflow_state in ("Draft", "Sent", "Received"):
            item["open_referrals"] += 1
            if record.due_date and frappe.utils.getdate(record.due_date) < today:
                item["overdue_referrals"] += 1
        completed = record.completed_on and frappe.utils.getdate(record.completed_on)
        if completed and from_date <= completed <= to_date:
            item["completed"] += 1
            item["complete_days"].append(days_between(record.sent_on, record.completed_on))

    if filters.get("organization"):
        units = {name: item for name, item in units.items() if name == filters["organization"]}

    data = []
    for name in sorted(units):
        item = units[name]
        data.append({
            "unit": name,
            "holding": item["holding"],
            "open_referrals": item["open_referrals"],
            "overdue_referrals": item["overdue_referrals"],
            "completed": item["completed"],
            "oldest_open": item["oldest_open"],
            "avg_complete_days": average(item["complete_days"]),
        })

    data.sort(key=lambda row: (row["overdue_referrals"], row["holding"]), reverse=True)

    columns = [
        {"label": _("Department"), "fieldname": "unit", "fieldtype": "Link",
         "options": "Department", "width": 190},
        _number_column("Holding Now", "holding"),
        _number_column("Open Referrals", "open_referrals"),
        _number_column("Overdue Referrals", "overdue_referrals"),
        _number_column("Completed in Period", "completed"),
        _number_column("Oldest Open (days)", "oldest_open"),
        _float_column("Average Days to Complete", "avg_complete_days"),
    ]

    total_holding = sum(item["holding"] for item in units.values())
    total_overdue = sum(item["overdue_referrals"] for item in units.values())
    most_loaded = max(data, key=lambda row: row["holding"], default=None)

    summary = [
        summary_item(_("Departments"), len(data)),
        summary_item(_("Files Held"), total_holding),
        summary_item(_("Overdue Referrals"), total_overdue,
                     indicator="Red" if total_overdue else "Gray"),
        summary_item(_("Most Held"), (most_loaded or {}).get("unit") or "-",
                     indicator="Orange" if most_loaded else "Gray"),
    ]

    top = data[:8]
    chart = {
        "data": {
            "labels": [row["unit"] for row in top],
            "datasets": [
                {"name": _("Holding Now"), "values": [row["holding"] for row in top]},
                {"name": _("Overdue Referrals"), "values": [row["overdue_referrals"] for row in top]},
            ],
        },
        "type": "bar",
        "colors": ["#2f6b5f", "#b03a2e"],
    }

    return columns, data, _(f"From {from_date} to {to_date}"), chart, summary
