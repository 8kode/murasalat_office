"""Central access-control rules for Murasalat Correspondence.

Frappe role permissions remain the baseline. This module adds document scope and
confidentiality enforcement without replacing Frappe's native User Permissions,
Document Sharing, Permission Levels, or custom Permission Types.
"""
import frappe
from murasalat_office.services.organization_context import get_memberships

ADMIN_ROLES = {"System Manager", "Murasalat Administrator", "Murasalat Auditor"}
CONFIDENTIAL_ACTIONS = {"view_confidential", "download_confidential"}


def _roles(user):
    return set(frappe.get_roles(user))


def _memberships(user):
    return get_memberships(user)


def _allowed_orgs(user):
    return {m.organization for m in _memberships(user) if m.organization}


def _clearance(user):
    rows = _memberships(user)
    return max([int(r.max_clearance_rank or 0) for r in rows] or [0])


def _is_privileged(user):
    return user == "Administrator" or bool(_roles(user) & ADMIN_ROLES)


def _rank(confidentiality):
    if not confidentiality:
        return 0
    return int(frappe.db.get_value("Murasalat Confidentiality Level", confidentiality, "clearance_rank") or 0)


def has_confidential_clearance(doc, user=None):
    user = user or frappe.session.user
    return _is_privileged(user) or _rank(doc.confidentiality) <= _clearance(user)


def can_access_attachment(doc, attachment, user=None, action="view"):
    user = user or frappe.session.user
    if not frappe.has_permission(doc, "read", user=user):
        return False
    if not attachment or not getattr(attachment, "is_secret", 0):
        return True
    if _is_privileged(user):
        return True
    perm = "download_confidential" if action == "download" else "view_confidential"
    return frappe.has_permission(doc, perm, user=user) and has_confidential_clearance(doc, user)


def get_permission_query_conditions(user=None):
    user = user or frappe.session.user
    if _is_privileged(user):
        return None

    orgs = sorted(_allowed_orgs(user))
    user_sql = frappe.db.escape(user)
    if not orgs:
        return "`tabMurasalat Correspondence`.`name` IN (SELECT parent FROM `tabMurasalat Referral` WHERE parenttype='Murasalat Correspondence' AND recipient_type='User' AND recipient_user={user})".format(user=user_sql)

    org_list = ", ".join(frappe.db.escape(o) for o in orgs)
    clearance = _clearance(user)
    confidential = "COALESCE((SELECT clearance_rank FROM `tabMurasalat Confidentiality Level` WHERE name=`tabMurasalat Correspondence`.`confidentiality`), 0) <= {clearance}".format(clearance=clearance)

    return """(
        {confidential} AND (
            `tabMurasalat Correspondence`.`owner`={user}
            OR `tabMurasalat Correspondence`.`source_entity` IN ({org_list})
            OR `tabMurasalat Correspondence`.`target_entity` IN ({org_list})
            OR `tabMurasalat Correspondence`.`current_holder` IN ({org_list})
            OR `tabMurasalat Correspondence`.`current_holder_user`={user}
            OR `tabMurasalat Correspondence`.`name` IN (
                SELECT parent FROM `tabMurasalat Referral`
                WHERE parenttype='Murasalat Correspondence' AND (
                    (recipient_type='User' AND recipient_user={user})
                    OR (recipient_type='Organization' AND recipient_organization IN ({org_list}))
                )
            )
        )
    )""".format(confidential=confidential, user=user_sql, org_list=org_list)


def has_permission(doc, user=None, permission_type=None):
    user = user or frappe.session.user
    if permission_type in CONFIDENTIAL_ACTIONS:
        return has_confidential_clearance(doc, user)
    if permission_type not in (None, "read", "select"):
        # Return None so Frappe continues its native role/custom-permission checks.
        return None
    if _is_privileged(user):
        return True
    if not has_confidential_clearance(doc, user):
        return False
    if doc.owner == user or doc.current_holder_user == user:
        return True
    orgs = _allowed_orgs(user)
    if {doc.source_entity, doc.target_entity, doc.current_holder} & orgs:
        return True
    for row in doc.referrals or []:
        if row.recipient_type == "User" and row.recipient_user == user:
            return True
        if row.recipient_type == "Organization" and row.recipient_organization in orgs:
            return True
    return None
