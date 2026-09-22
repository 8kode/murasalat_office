"""Read-only audit of native Frappe/ERPNext governance configuration.

This module never creates, mutates, or requires roles, permissions, workflows,
or workflow states. Site administrators own all of those settings in Desk.
"""
import frappe

GOVERNED_DOCTYPES = (
    "Murasalat Correspondence",
    "Murasalat Approval Request",
    "Murasalat Referral",
    "Murasalat Delegation",
    "Murasalat User Organization Membership",
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

    checks.extend(workflow_task_readiness())

    return {
        "status": "FAIL" if any(c["status"] == "FAIL" for c in checks) else "WARN" if any(c["status"] == "WARN" for c in checks) else "PASS",
        "checks": checks,
        "governed_doctypes": list(GOVERNED_DOCTYPES),
        "governance_mode": "native_frappe_desk",
    }


def workflow_task_readiness():
    """Report whether native Workflow transitions actually call the lifecycle hooks.

    Read-only: this never creates a Workflow, a Workflow Transition Tasks
    document, or a hook. It reports what Desk currently dispatches, because a
    declared hook does not run until a transition carries a matching task.
    """
    checks = []

    def add(key, title, status, details, remediation=""):
        checks.append({"key": key, "title": title, "status": status, "details": details, "remediation": remediation})

    if not _exists("Workflow Transition Tasks"):
        return checks

    declared = {}
    for entry in frappe.get_hooks("workflow_methods") or []:
        if isinstance(entry, dict) and entry.get("name"):
            declared[entry["name"]] = entry.get("method")

    if not declared:
        add(
            "workflow_tasks:hooks",
            "Workflow lifecycle hooks",
            "FAIL",
            "No workflow_methods entry is declared by the application.",
            "Verify the installed application version and run bench migrate.",
        )
        return checks

    groups = {}
    rows = frappe.get_all(
        "Workflow Transition Task",
        fields=["parent", "task", "enabled", "asynchronous"],
        limit_page_length=500,
    )
    for row in rows:
        groups.setdefault(row["parent"], []).append(row)

    workflows = []
    if _exists("Workflow"):
        workflows = frappe.get_all(
            "Workflow",
            filters={"is_active": 1, "document_type": ["in", list(GOVERNED_DOCTYPES)]},
            fields=["name", "document_type"],
            limit_page_length=100,
        )

    for workflow in workflows:
        doc = frappe.get_doc("Workflow", workflow["name"])
        unattached = []

        for transition in doc.transitions or []:
            if not transition.transition_tasks:
                unattached.append(transition.action)
                continue

            group_rows = groups.get(transition.transition_tasks, [])
            key = f"workflow_tasks:{workflow['name']}:{transition.action}"
            title = f"{workflow['name']}: {transition.action}"

            if not group_rows:
                add(
                    key,
                    title,
                    "WARN",
                    f"Transition Tasks points at {transition.transition_tasks}, which has no task rows.",
                    "Add the lifecycle task row to that Workflow Transition Tasks document.",
                )
                continue

            for row in group_rows:
                if row["task"] not in declared:
                    add(
                        key,
                        title,
                        "FAIL",
                        f"Task {row['task']} is not declared by this application's workflow_methods hook.",
                        "Use an exact hook name. An unknown task name makes every transition that uses it throw.",
                    )
                elif not row["enabled"]:
                    add(
                        key,
                        title,
                        "INFO",
                        f"Task {row['task']} is disabled, so it will not run.",
                        "Enable the row if this transition should write lifecycle fields.",
                    )
                elif row["asynchronous"]:
                    add(
                        key,
                        title,
                        "WARN",
                        f"Task {row['task']} is asynchronous. The method mutates the in-memory document and relies on the transition's own save, so an asynchronous run persists nothing.",
                        "Clear Asynchronous so the method runs inside the transition transaction.",
                    )
                else:
                    add(
                        key,
                        title,
                        "PASS",
                        f"Task {row['task']} will run synchronously inside the transition.",
                        "",
                    )

        if unattached:
            add(
                f"workflow_tasks:{workflow['name']}:unattached",
                f"{workflow['name']}: transitions without transition tasks",
                "WARN",
                "These transitions run no application lifecycle code: " + ", ".join(unattached) + ".",
                "Attach a Workflow Transition Tasks document to each transition that should write lifecycle fields.",
            )

    return checks
