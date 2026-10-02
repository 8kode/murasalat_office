"""Make a site launchable, in one command, without shipping governance as fixtures.

A fresh install needs master data, native permissions, notification configuration and site-defined
Workflows. Workflow design is deliberately outside this application: the institution creates and
maintains its own Workflows in Desk. This application exposes optional Transition Task methods and
reports whether native Workflows exist, but never creates or mutates them.

Staying in Desk is the point of this application: `hooks.py` ships no `fixtures`, so nothing here
is silently applied on install or migrate.

Nothing happens without `confirm=True`, and every step is idempotent - an existing Workflow is
reported, never overwritten, because an administrator may have edited it.

    bench --site <site> execute murasalat_office.setup.provision.readiness
    bench --site <site> execute murasalat_office.setup.provision.apply \
        --kwargs "{'confirm': True}"

The Workflow fieldnames are read from the live `meta` rather than hardcoded: they are the
framework's, not ours, and a renamed field should surface as a clear message instead of a
half-built Workflow.
"""
import frappe
from frappe import _

from murasalat_office.setup import (
    governance_plan,
    master_data,
    notifications,
    report_print_formats,
)

CORRESPONDENCE = "Murasalat Correspondence"
REFERRAL = "Murasalat Referral"

CLERK = "Correspondence Clerk"
SUPERVISOR = "Correspondence Supervisor"
CREATE_REPLY_PERMISSION = "create_reply"

# No Workflow is shipped or created here. Workflow state names and transitions belong to the
# institution. The application only exposes optional lifecycle methods through hooks.py.




def ensure_custom_permission_type(confirm=False):
    """Create the native v16 Permission Type used by the Create Reply action.

    Permission Types are site governance, not app fixtures. They are created explicitly during
    the confirmed provisioning command so an administrator can review and rerun the operation.
    The live DocType metadata is used for the document-type field name because Frappe has used
    ``doc_type`` for this record in v16.
    """
    if not confirm:
        frappe.throw(
            _("Creating the Create Reply permission requires confirm=True.")
        )

    meta = frappe.get_meta("Permission Type")
    doc_type_field = "doc_type" if meta.get_field("doc_type") else "document_type"
    if not meta.get_field(doc_type_field) or not meta.get_field("perm_type"):
        frappe.throw(
            _("This Frappe version does not expose the expected Permission Type fields.")
        )

    filters = {
        doc_type_field: CORRESPONDENCE,
        "perm_type": CREATE_REPLY_PERMISSION,
    }
    existing = frappe.db.exists("Permission Type", filters)
    if existing:
        return {"name": existing, "created": False, "perm_type": CREATE_REPLY_PERMISSION}

    doc = frappe.get_doc({
        "doctype": "Permission Type",
        doc_type_field: CORRESPONDENCE,
        "perm_type": CREATE_REPLY_PERMISSION,
    })
    doc.insert(ignore_permissions=True)

    return {"name": doc.name, "created": True, "perm_type": CREATE_REPLY_PERMISSION}


def plan():
    """Read-only: what provisioning would create, and what is already there."""
    roles = {role: frappe.db.exists("Role", role) for role in governance_plan.PERMISSION_PLAN}

    workflows = []
    for doctype in (CORRESPONDENCE, REFERRAL):
        rows = frappe.get_all(
            "Workflow",
            filters={"document_type": doctype, "is_active": 1},
            fields=["name"],
            limit_page_length=50,
        )
        workflows.append({
            "document_type": doctype,
            "active_workflows": rows,
            "site_defined": True,
        })

    permission_type_exists = frappe.db.exists(
        "Permission Type",
        {"perm_type": CREATE_REPLY_PERMISSION, "doc_type": CORRESPONDENCE},
    )

    return {
        "master_data_missing": master_data.verify(),
        "create_reply_permission_type_present": bool(permission_type_exists),
        "roles_present": roles,
        "roles_to_create": [r for r, present in roles.items() if not present],
        "workflows": workflows,
    }



def apply(confirm=False):
    """Create site-independent master/governance building blocks only.

    No Workflow is created or modified. The institution defines both document Workflows
    from Desk, and may attach the application's optional Transition Tasks to its chosen
    transitions.
    """
    if not confirm:
        frappe.throw(
            _("This writes master data, permission types, roles and native notification configuration. Re-run with confirm=True.")
        )

    report = {
        "master_data": master_data.seed(),
        "permission_type": ensure_custom_permission_type(confirm=True),
        "roles": governance_plan.materialize(confirm=True),
        "print_formats": report_print_formats.install(),
        "notifications": notifications.install(),
        "notification_plan": notifications.plan(),
        "workflows": "site_defined_no_changes",
        "errors": [],
    }
    return report


def readiness():
    """Read-only launch/readiness report; never creates or modifies Workflows."""
    checks = []
    missing = master_data.verify()
    checks.append(("master data", "ok" if not missing else f"{len(missing)} missing", not missing))

    permission_type_exists = frappe.db.exists(
        "Permission Type",
        {"perm_type": CREATE_REPLY_PERMISSION, "doc_type": CORRESPONDENCE},
    )
    checks.append(("permission type create_reply", "ok" if permission_type_exists else "not created", bool(permission_type_exists)))

    roles = [role for role in governance_plan.PERMISSION_PLAN if not frappe.db.exists("Role", role)]
    checks.append(("roles", "ok" if not roles else f"missing {roles}", not roles))

    for doctype in (CORRESPONDENCE, REFERRAL):
        workflows = frappe.get_all(
            "Workflow",
            filters={"document_type": doctype, "is_active": 1},
            fields=["name"],
            limit_page_length=50,
        )
        checks.append((
            f"active workflow {doctype}",
            "ok" if workflows else "not configured (optional)",
            True,
        ))

    result = {
        "checks": [
            {"name": name, "status": status, "ok": ok}
            for name, status, ok in checks
        ],
        "ready": all(ok for _, _, ok in checks),
        "workflow_policy": "institution_defined",
    }
    return result

