"""Attach the lifecycle methods to workflow transitions.

A ``workflow_methods`` hook does not fire on its own. ``apply_workflow`` runs the hooks it
finds through a *transition task*: a ``Workflow Transition Task`` row whose ``task`` names
an entry in ``workflow_methods``, attached to a transition through the transition's
``transition_tasks`` link. Until those rows exist, the transition moves the workflow state
and nothing else happens — no registration, no sealing, no referral stamping.

Two entry points, both idempotent and safe to re-run:

    bench --site <site> execute murasalat_office.setup.workflow_tasks.plan    # read-only
    bench --site <site> execute murasalat_office.setup.workflow_tasks.apply

``plan`` prints exactly what ``apply`` would create, so the change can be reviewed before
it is made.

**Frappe version note.** Transition tasks are implemented in Frappe develop (v16) and are
absent from version-15, where ``apply_workflow`` contains no transition-task handling at
all. On version-15 no amount of configuration makes these hooks fire from a transition;
``plan`` reports that plainly instead of producing a configuration that cannot work.
"""
GROUP_DOCTYPE = "Workflow Transition Tasks"
CHILD_DOCTYPE = "Workflow Transition Task"
LINK_FIELD = "transition_tasks"


def hook_names():
    """The names of the app's registered workflow_methods, in declaration order."""
    import frappe

    entries = frappe.get_hooks("workflow_methods") or []
    return [entry.get("name") for entry in entries if entry.get("name")]


def supports_transition_tasks():
    import frappe

    return frappe.get_meta("Workflow Transition").has_field(LINK_FIELD)


def _child_fieldname():
    """The Table field on the group doctype that holds the transition-task rows."""
    import frappe

    for field in frappe.get_meta(GROUP_DOCTYPE).fields:
        if field.fieldtype == "Table" and field.options == CHILD_DOCTYPE:
            return field.fieldname

    return None


def collect():
    """Every (workflow, transition, hook) that needs a task row.

    Pure read: returns a list of dicts, creates nothing.
    """
    import frappe

    wanted = set(hook_names())
    plan = []

    for workflow in frappe.get_all(
        "Workflow", filters={"is_active": 1}, fields=["name", "document_type"], limit_page_length=0
    ):
        transitions = frappe.get_all(
            "Workflow Transition",
            filters={"parent": workflow.name},
            fields=["name", "action", "state", "next_state"],
            order_by="idx",
            limit_page_length=0,
        )

        for transition in transitions:
            if transition.action not in wanted:
                continue

            existing = None

            if supports_transition_tasks():
                existing = frappe.db.get_value("Workflow Transition", transition.name, LINK_FIELD)

            plan.append(
                {
                    "workflow": workflow.name,
                    "doctype": workflow.document_type,
                    "transition": transition.name,
                    "action": transition.action,
                    "from": transition.state,
                    "to": transition.next_state,
                    "hook": transition.action,
                    "attached": bool(existing),
                }
            )

    return plan


def plan():
    """Print what apply would do. Changes nothing."""
    print("Murasalat Office transition tasks")
    print("=" * 40)

    if not supports_transition_tasks():
        print(
            "This Frappe version does not implement transition tasks, so a workflow_methods\n"
            "hook cannot be attached to a transition here. Options:\n"
            "  1. run this app on a Frappe version that implements transition tasks; or\n"
            "  2. call the lifecycle methods from a Server Script or a doc_events hook."
        )
        return []

    rows = collect()

    if not rows:
        print("No transition matches a registered workflow_methods name.")
        return rows

    for row in rows:
        state = "attached" if row["attached"] else "needs a task"
        print(
            f"  {row['action']:<24} {row['from']} -> {row['to']:<24} "
            f"hook={row['hook']:<24} {state}"
        )

    pending = [row for row in rows if not row["attached"]]
    print("=" * 40)
    print(f"{len(rows)} transition(s) map to a hook, {len(pending)} still need a task")

    return rows


def apply():
    """Create the missing transition-task groups and attach them. Idempotent."""
    import frappe

    if not supports_transition_tasks():
        print("This Frappe version does not implement transition tasks; nothing to do.")
        return []

    if not frappe.db.exists("DocType", GROUP_DOCTYPE):
        print(f"{GROUP_DOCTYPE} does not exist on this site; nothing to do.")
        return []

    child_field = _child_fieldname()

    if not child_field:
        print(f"{GROUP_DOCTYPE} has no table field pointing at {CHILD_DOCTYPE}; nothing to do.")
        return []

    hooks = {entry.get("name"): entry.get("method") for entry in (frappe.get_hooks("workflow_methods") or [])}
    attached = []

    for row in collect():
        if row["attached"]:
            print(f"  ok    {row['action']}")
            continue

        group = frappe.get_doc(
            {
                "doctype": GROUP_DOCTYPE,
                child_field: [
                    {
                        "doctype": CHILD_DOCTYPE,
                        "task": row["hook"],
                        "enabled": 1,
                        # Inline, in the transition's own transaction. An asynchronous task
                        # would run after the transition, outside its save.
                        "asynchronous": 0,
                    }
                ],
            }
        ).insert(ignore_permissions=True)

        workflow = frappe.get_doc("Workflow", row["workflow"])

        for transition in workflow.transitions:
            if transition.name == row["transition"]:
                transition.set(LINK_FIELD, group.name)

        workflow.save(ignore_permissions=True)

        attached.append(row["action"])
        print(f"  set   {row['action']} -> {hooks.get(row['hook'], row['hook'])} ({group.name})")

    frappe.db.commit()

    print(f"{len(attached)} transition task(s) created")
    return attached
