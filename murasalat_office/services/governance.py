"""Read-only audit of native Frappe/ERPNext governance configuration.

This module never creates, mutates, or requires roles, permissions, workflows,
or workflow states. Site administrators own all of those settings in Desk.
"""
import frappe

GOVERNED_DOCTYPES = (
    "Murasalat Correspondence",
    "Murasalat Approval Request",
    "Murasalat Referral",
)


def _exists(doctype):
    try:
        return bool(frappe.db.exists("DocType", doctype))
    except Exception:
        return False


def governance_health():
    checks = []

    def add(key, title, status, details, remediation=""):
        checks.append({"key": key, "title": title, "status": status, "details": details, "remediation": remediation})

    for doctype in GOVERNED_DOCTYPES:
        if not _exists(doctype):
            add(f"doctype:{doctype}", doctype, "FAIL", "DocType is missing.")
            continue
        perms = frappe.get_all(
            "DocPerm",
            filters={"parent": doctype, "parenttype": "DocType"},
            fields=["role", "read", "write", "create", "delete", "submit", "cancel", "amend", "report", "export", "import", "share", "print", "email"],
            limit_page_length=500,
        )
        add(
            f"role_perms:{doctype}",
            f"Role Permission Manager: {doctype}",
            "PASS" if perms else "WARN",
            f"{len(perms)} native DocPerm rows are currently configured." if perms else "No native DocPerm rows are configured.",
            "Configure permissions from Role Permission Manager." if not perms else "",
        )

    workflows = []
    if _exists("Workflow"):
        workflows = frappe.get_all(
            "Workflow",
            filters={"is_active": 1, "document_type": ["in", list(GOVERNED_DOCTYPES)]},
            fields=["name", "document_type", "workflow_state_field", "allow_self_approval"],
            limit_page_length=100,
        )
    by_doctype = {w["document_type"]: w for w in workflows}
    for doctype in GOVERNED_DOCTYPES:
        workflow = by_doctype.get(doctype)
        if not workflow:
            add(
                f"workflow:{doctype}",
                f"Active Workflow: {doctype}",
                "INFO",
                "No active native Workflow is configured. This is valid: Workflow is optional and entirely controlled from Desk.",
                "Create or activate a Workflow from Settings > Workflow if this document needs governed transitions.",
            )
            continue
        doc = frappe.get_doc("Workflow", workflow["name"])
        add(
            f"workflow:{doctype}",
            f"Active Workflow: {doctype}",
            "PASS",
            f"{workflow['name']} is active with {len(doc.states or [])} states and {len(doc.transitions or [])} transitions. Self approval={'enabled' if workflow.get('allow_self_approval') else 'disabled'}.",
            "Edit the Workflow in Desk; the application does not enforce a fixed state model.",
        )

    return {
        "status": "FAIL" if any(c["status"] == "FAIL" for c in checks) else "WARN" if any(c["status"] == "WARN" for c in checks) else "PASS",
        "checks": checks,
        "governed_doctypes": list(GOVERNED_DOCTYPES),
        "governance_mode": "native_frappe_erpnext_desk",
    }
