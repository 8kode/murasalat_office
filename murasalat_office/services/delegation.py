import frappe
from frappe.utils import getdate, today

ACTION_FIELD = {
    "receive": "allow_receive",
    "start": "allow_start",
    "complete": "allow_complete",
    "reject": "allow_reject",
    "return": "allow_return",
}

def get_active_delegation(delegator, delegate, organization=None, action=None):
    filters = {"delegator": delegator, "delegate": delegate, "enabled": 1}
    rows = frappe.get_all("Murasalat Delegation", filters=filters, fields=["name","organization","from_date","to_date",*ACTION_FIELD.values()])
    current = getdate(today())
    for row in rows:
        if not (getdate(row.from_date) <= current <= getdate(row.to_date)):
            continue
        if row.organization and organization and row.organization != organization:
            continue
        if row.organization and not organization:
            continue
        if action and not row.get(ACTION_FIELD.get(action, "")):
            continue
        return row
    return None

def can_act_for(delegator, actor, organization=None, action=None):
    if actor == delegator:
        return {"authorized": True, "delegation": None, "acting_for": None}
    delegation = get_active_delegation(delegator, actor, organization, action)
    return {"authorized": bool(delegation), "delegation": delegation.name if delegation else None, "acting_for": delegator if delegation else None}
