"""Active organizational context built on Frappe User Defaults.

A user may belong to several organizational entities. Membership answers where a user
*may* act; the active context answers which organization the user is currently acting
for in a Desk session. The context is intentionally stored in Frappe's native defaults
instead of duplicating user/session state in a custom DocType.
"""
import frappe
from frappe import _
from frappe.utils import getdate, today

DEFAULT_KEY = "murasalat_active_organization"


def get_memberships(user=None):
    user = user or frappe.session.user
    rows = frappe.get_all(
        "Murasalat User Organization Membership",
        filters={"user": user, "enabled": 1},
        fields=["name", "organization", "access_level", "max_clearance_rank", "valid_from", "valid_to"],
    )
    now = getdate(today())
    return [
        row for row in rows
        if (not row.valid_from or getdate(row.valid_from) <= now)
        and (not row.valid_to or getdate(row.valid_to) >= now)
    ]


def get_active_organization(user=None, require=False):
    user = user or frappe.session.user
    memberships = get_memberships(user)
    allowed = {row.organization for row in memberships}
    active = frappe.defaults.get_user_default(DEFAULT_KEY, user=user)

    if active in allowed:
        return active

    if active and active not in allowed:
        frappe.defaults.clear_user_default(DEFAULT_KEY, user=user)

    if len(allowed) == 1:
        only = next(iter(allowed))
        frappe.defaults.set_user_default(DEFAULT_KEY, only, user=user)
        return only

    if require:
        frappe.throw(_("Select an active Murasalat organization before performing this operation."))
    return None


def set_active_organization(organization, user=None):
    user = user or frappe.session.user
    if user == "Administrator":
        if organization and not frappe.db.exists("Murasalat Organization Entity", organization):
            frappe.throw(_("Organization not found."))
    else:
        allowed = {row.organization for row in get_memberships(user)}
        if organization not in allowed:
            frappe.throw(_("You are not an active member of the selected organization."), frappe.PermissionError)
    frappe.defaults.set_user_default(DEFAULT_KEY, organization, user=user)
    return get_context(user)


def clear_active_organization(user=None):
    user = user or frappe.session.user
    frappe.defaults.clear_user_default(DEFAULT_KEY, user=user)
    return get_context(user)


def get_context(user=None):
    user = user or frappe.session.user
    memberships = get_memberships(user)
    return {
        "active_organization": get_active_organization(user),
        "memberships": [
            {
                "organization": row.organization,
                "access_level": row.access_level,
                "max_clearance_rank": row.max_clearance_rank,
                "valid_from": row.valid_from,
                "valid_to": row.valid_to,
            }
            for row in memberships
        ],
    }


@frappe.whitelist()
def get_current_context():
    return get_context()


@frappe.whitelist()
def select_active_organization(organization):
    return set_active_organization(organization)
