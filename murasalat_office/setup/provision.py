"""Make a site launchable, in one command, without shipping governance as fixtures.

A fresh install needs six things before the first user can work: master data, roles and their
permission rows, two Workflows with their transitions, one task attached to each transition,
an Assignment Rule, and a Department with users. Five of those are Desk configuration - and
staying in Desk is the point of this application: `hooks.py` ships no `fixtures`, so nothing
here is applied on install or on migrate.

What was missing was a single, reviewable way to *create* that configuration through Frappe's
own models, which is exactly what clicking through Desk does. `governance_plan.materialize`
already did it for roles. This module completes it: it builds the Workflows and attaches the
lifecycle tasks, then reports whether the site is actually launchable.

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

# Draft is the state a new record starts in, and every DocType here is non-submittable, so all
# states sit at doc_status 0.
WORKFLOWS = [
    {
        "name": "Murasalat Correspondence Lifecycle",
        "document_type": CORRESPONDENCE,
        "states": [
            {"state": "Draft", "allow_edit": CLERK},
            {"state": "Registered", "allow_edit": CLERK},
            {"state": "Closed", "allow_edit": SUPERVISOR},
            {"state": "Sealed", "allow_edit": SUPERVISOR},
        ],
        "transitions": [
            {"state": "Draft", "action": "Register", "next_state": "Registered",
             "allowed": CLERK, "task": "Register Correspondence"},
            {"state": "Registered", "action": "Close", "next_state": "Closed",
             "allowed": CLERK, "task": "Close Correspondence"},
            {"state": "Closed", "action": "Seal", "next_state": "Sealed",
             "allowed": SUPERVISOR, "task": "Seal Correspondence"},
            {"state": "Sealed", "action": "Reopen", "next_state": "Registered",
             "allowed": SUPERVISOR, "task": "Reopen Correspondence"},
        ],
    },
    {
        "name": "Murasalat Referral Lifecycle",
        "document_type": REFERRAL,
        "states": [
            {"state": "Draft", "allow_edit": CLERK},
            {"state": "Sent", "allow_edit": CLERK},
            {"state": "Received", "allow_edit": CLERK},
            {"state": "Completed", "allow_edit": CLERK},
            {"state": "Cancelled", "allow_edit": CLERK},
        ],
        "transitions": [
            {"state": "Draft", "action": "Send", "next_state": "Sent",
             "allowed": CLERK, "task": "Send Referral"},
            {"state": "Sent", "action": "Receive", "next_state": "Received",
             "allowed": CLERK, "task": "Receive Referral"},
            {"state": "Received", "action": "Complete", "next_state": "Completed",
             "allowed": CLERK, "task": "Complete Referral"},
            # Cancellation is the terminal alternative to completion. `cancel_referral` shipped
            # before the transition that calls it, so the method, its mandatory reason and the
            # close condition that stops the reminders had nothing to run them.
            {"state": "Draft", "action": "Cancel", "next_state": "Cancelled",
             "allowed": CLERK, "task": "Cancel Referral"},
            {"state": "Sent", "action": "Cancel", "next_state": "Cancelled",
             "allowed": CLERK, "task": "Cancel Referral"},
            {"state": "Received", "action": "Cancel", "next_state": "Cancelled",
             "allowed": CLERK, "task": "Cancel Referral"},
        ],
    },
    {
        # Two states and two transitions, on purpose: every transition carries its task, which is
        # the invariant this module holds everywhere else. A request is created to be decided, so
        # it starts at the state where the decision is made - and the only way back is the
        # documented one, returning an approved request for amendment.
        "name": "Murasalat Approval Workflow",
        "document_type": "Murasalat Approval Request",
        "states": [
            {"state": "Pending Approval", "allow_edit": SUPERVISOR},
            {"state": "Approved", "allow_edit": SUPERVISOR},
        ],
        "transitions": [
            {"state": "Pending Approval", "action": "Approve", "next_state": "Approved",
             "allowed": SUPERVISOR, "task": "Stamp Approval"},
            {"state": "Approved", "action": "Return for Amendment", "next_state": "Pending Approval",
             "allowed": SUPERVISOR, "task": "Clear Approval"},
        ],
    },
]

STATE_FIELD = "workflow_state"


def _field(meta, *candidates):
    """The first of these fieldnames that the live DocType actually declares.

    A framework fieldname is not ours to assume. Failing here names what was looked for and
    what the DocType offers, so a mismatch is a one-line fix rather than a broken Workflow.
    """
    for candidate in candidates:
        if meta.get_field(candidate):
            return candidate

    available = sorted(f.fieldname for f in meta.fields)
    frappe.throw(
        _("None of {0} exists on {1}. Available fields: {2}").format(
            ", ".join(candidates), meta.name, ", ".join(available)
        )
    )


def _workflow_fieldnames():
    meta = frappe.get_meta("Workflow")

    return {
        "state_field": _field(meta, "workflow_state_field"),
        "active": _field(meta, "is_active"),
        "states": _field(meta, "states"),
        "transitions": _field(meta, "transitions"),
        "state_meta": frappe.get_meta("Workflow Document State"),
        "transition_meta": frappe.get_meta("Workflow Transition"),
        "group_meta": frappe.get_meta("Workflow Transition Tasks"),
        "task_meta": frappe.get_meta("Workflow Transition Task"),
    }


def _transition_task_field(transition_meta):
    """How a transition points at its task group - the name varies across releases."""
    return _field(transition_meta, "transition_tasks", "transition_task", "task")


def plan():
    """Read-only: what provisioning would create, and what is already there."""
    roles = {role: frappe.db.exists("Role", role) for role in governance_plan.PERMISSION_PLAN}

    workflows = []
    for spec in WORKFLOWS:
        exists = frappe.db.exists("Workflow", spec["name"])
        transitions = [] if exists else [t["action"] for t in spec["transitions"]]
        workflows.append({
            "workflow": spec["name"],
            "document_type": spec["document_type"],
            "exists": bool(exists),
            "would_create_transitions": transitions,
        })

    return {
        "master_data_missing": master_data.verify(),
        "roles_present": roles,
        "roles_to_create": [r for r, present in roles.items() if not present],
        "workflows": workflows,
    }


def _task_group_name(workflow_name):
    return workflow_name  # one group per workflow, named the same, so it is obvious in Desk


def _ensure_task_group(spec, names):
    group_meta, task_meta = names["group_meta"], names["task_meta"]
    group_name = _task_group_name(spec["name"])

    tasks_field = _field(group_meta, "tasks")
    task_field = _field(task_meta, "task")
    enabled_field = _field(task_meta, "enabled")
    async_field = _field(task_meta, "asynchronous")

    if frappe.db.exists("Workflow Transition Tasks", group_name):
        return group_name, "exists"

    document = frappe.get_doc({"doctype": "Workflow Transition Tasks", "name": group_name})
    document.set(tasks_field, [])

    for transition in spec["transitions"]:
        row = document.append(tasks_field, {})
        row.set(task_field, transition["task"])
        row.set(enabled_field, 1)
        # Asynchronous runs the method outside the transition's transaction, which turns every
        # lifecycle method into a silent no-op - the failure WORKFLOW_GOVERNANCE.md documents.
        row.set(async_field, 0)

    document.insert(ignore_permissions=True)

    return group_name, "created"


def _top_up_transition_tasks(spec, names):
    """Add a task row for any transition that needs one and has none. Never edits a row.

    ``_ensure_workflow`` returns early for a Workflow that already exists - on purpose, because an
    administrator may have edited it. The cost of that promise is this hole: a site whose Workflow
    was created before the transition-task feature, or by hand in Desk, keeps transitions that run
    no lifecycle method. Frappe changes the state and writes nothing, so a referral is sent with no
    ``sent_on``, is received with no ``received_on``, and every panel that reads those fields
    contradicts the state shown beside it. Nothing reports it, because nothing is broken enough to
    throw.

    So the Workflow is still never overwritten, and the tasks are still completed: missing rows are
    appended, existing ones are left exactly as they are.
    """
    group_name = _task_group_name(spec["name"])

    if not frappe.db.exists("Workflow Transition Tasks", group_name):
        _ensure_task_group(spec, names)
        return {"group": group_name, "attached": [t["task"] for t in spec["transitions"]],
                "outcome": "created"}

    group_meta, task_meta = names["group_meta"], names["task_meta"]
    tasks_field = _field(group_meta, "tasks")
    task_field = _field(task_meta, "task")
    enabled_field = _field(task_meta, "enabled")
    async_field = _field(task_meta, "asynchronous")

    document = frappe.get_doc("Workflow Transition Tasks", group_name)
    present = {
        row.get(task_field) for row in document.get(tasks_field) or [] if row.get(task_field)
    }
    missing = [t["task"] for t in spec["transitions"] if t["task"] not in present]

    if not missing:
        return {"group": group_name, "attached": [], "outcome": "complete"}

    for task in missing:
        row = document.append(tasks_field, {})
        row.set(task_field, task)
        row.set(enabled_field, 1)
        # Asynchronous runs the method outside the transition's transaction, which turns every
        # lifecycle method into a silent no-op - the failure WORKFLOW_GOVERNANCE.md documents.
        row.set(async_field, 0)

    document.save(ignore_permissions=True)

    return {"group": group_name, "attached": missing, "outcome": "topped up"}


def _ensure_workflow(spec, names):
    if frappe.db.exists("Workflow", spec["name"]):
        return "exists"

    task_field = _transition_task_field(names["transition_meta"])
    group_name, _ = _ensure_task_group(spec, names)

    document = frappe.get_doc({
        "doctype": "Workflow",
        "workflow_name": spec["name"],
        "document_type": spec["document_type"],
        names["state_field"]: STATE_FIELD,
        names["active"]: 1,
    })

    state_meta, transition_meta = names["state_meta"], names["transition_meta"]
    state_name = _field(state_meta, "state")
    doc_status = _field(state_meta, "doc_status")
    allow_edit = _field(transition_meta, "allow_edit")

    for state in spec["states"]:
        row = document.append(names["states"], {})
        row.set(state_name, state["state"])
        row.set("state", state["state"])
        row.set(doc_status, "0")
        row.set(allow_edit, state["allow_edit"])

    for transition in spec["transitions"]:
        row = document.append(names["transitions"], {})
        row.set("state", transition["state"])
        row.set("action", transition["action"])
        row.set("next_state", transition["next_state"])
        row.set("allowed", transition["allowed"])
        row.set(allow_edit, transition["allowed"])
        row.set(task_field, group_name)

    document.insert(ignore_permissions=True)

    return "created"


def apply(confirm=False):
    """Create what is missing. Refuses to run without confirm=True."""
    if not confirm:
        frappe.throw(
            _("This writes roles, permissions and Workflows. Re-run with confirm=True.")
        )

    report = {
        "master_data": None,
        "roles": [],
        "workflows": [],
        "print_formats": None,
        "notifications": None,
        "errors": [],
    }

    report["master_data"] = master_data.seed()
    report["roles"] = governance_plan.materialize(confirm=True)
    report["print_formats"] = report_print_formats.install()
    report["notifications"] = notifications.install()

    try:
        names = _workflow_fieldnames()
    except Exception as exc:
        report["errors"].append(str(exc))
        return report

    for spec in WORKFLOWS:
        try:
            outcome = _ensure_workflow(spec, names)
            # Then, and for a Workflow that already existed too: a transition with no task runs
            # no application code and reports nothing at all.
            tasks = _top_up_transition_tasks(spec, names)
            report["workflows"].append({
                "workflow": spec["name"],
                "outcome": outcome,
                "transition_tasks": tasks,
            })
        except Exception as exc:
            report["errors"].append(f"{spec['name']}: {exc}")

    return report


def _unattached_transitions(spec):
    """Transition actions in a live Workflow that carry no task row of their own."""
    group_name = _task_group_name(spec["name"])

    if not frappe.db.exists("Workflow Transition Tasks", group_name):
        return [t["action"] for t in spec["transitions"]]

    try:
        names = _workflow_fieldnames()
        group_meta, task_meta = names["group_meta"], names["task_meta"]
        tasks_field = _field(group_meta, "tasks")
        task_field = _field(task_meta, "task")

        document = frappe.get_doc("Workflow Transition Tasks", group_name)
        present = {
            row.get(task_field) for row in document.get(tasks_field) or [] if row.get(task_field)
        }
    except Exception:  # noqa: BLE001 - an unreadable group is reported, not thrown
        return [t["action"] for t in spec["transitions"]]

    return [t["action"] for t in spec["transitions"] if t["task"] not in present]


def readiness():
    """Is this site launchable? Prints the answer and returns it as a dict.

    Every line is a check a person can act on. It reads only.
    """
    checks = []

    missing = master_data.verify()
    checks.append(("master data", "ok" if not missing else f"{len(missing)} missing", not missing))

    roles = [role for role in governance_plan.PERMISSION_PLAN
             if not frappe.db.exists("Role", role)]
    checks.append(("roles", "ok" if not roles else f"missing {roles}", not roles))

    for spec in WORKFLOWS:
        exists = frappe.db.exists("Workflow", spec["name"])
        checks.append((f"workflow {spec['name']}", "ok" if exists else "not created", bool(exists)))

        # A Workflow that exists is not the same as a Workflow that works: its transitions run
        # nothing until each one carries its task. Reported separately, because the remedy is a
        # command rather than a rebuild.
        if not exists:
            continue

        missing = _unattached_transitions(spec)
        checks.append((
            f"transition tasks {spec['name']}",
            "ok" if not missing else f"{len(missing)} transition(s) run no method: {missing}",
            not missing,
        ))

    plan = notifications.plan()
    for row in plan["notifications"]:
        ok = bool(row["exists"] and row["current"])
        detail = "ok" if ok else ("not created" if not row["exists"] else "out of date")
        checks.append((f"notification {row['notification']}", detail, ok))

    rule = plan["assignment_rule"]
    ok = bool(rule["exists"] and rule["current"])
    detail = "ok" if ok else ("not created" if not rule["exists"] else "out of date")
    checks.append((f"assignment rule {rule['rule']}", detail, ok))

    try:
        from murasalat_office.services.governance import workflow_task_readiness
        wired = workflow_task_readiness()
        problems = wired.get("problems") or wired.get("issues") or []
        checks.append(("transition tasks", "ok" if not problems else f"{len(problems)} problem(s)",
                       not problems))
    except Exception as exc:
        checks.append(("transition tasks", f"could not read ({exc})", False))

    print("Murasalat launch readiness")
    print("-" * 46)
    for name, detail, ok in checks:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:34s} {detail}")

    ready = all(ok for _, _, ok in checks)
    print("-" * 46)
    print("Ready for users." if ready else "Not ready - see the FAIL lines above.")

    return {"ready": ready, "checks": [
        {"name": n, "detail": d, "ok": ok} for n, d, ok in checks
    ]}
