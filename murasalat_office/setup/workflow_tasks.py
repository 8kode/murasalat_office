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


def hook_methods():
    """Map each registered workflow_methods name to the method it will call."""
    import frappe

    entries = frappe.get_hooks("workflow_methods") or []
    return {entry.get("name"): entry.get("method") for entry in entries if entry.get("name")}


def hook_names():
    """The names of the app's registered workflow_methods, in declaration order."""
    return list(hook_methods())


def HOOK_METHODS():  # noqa: N802 - kept as a name so plan reads naturally
    return hook_methods()


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


def suggest_group_name(workflow_name, action):
    """A readable group name, following the convention already used on the site.

    The site's existing groups read "Murasalat Referral Send Task", "Murasalat
    Correspondence Seal Task" and so on: the workflow name without its "Workflow" suffix,
    then the action, then "Task".
    """
    prefix = workflow_name.replace(" Workflow", "").strip()
    return f"{prefix} {action} Task"


def unique_group_name(base):
    """The base name, or the first free numbered variant of it.

    ``Workflow Transition Tasks`` names its documents by prompting, so the name has to be
    supplied on insert and must not collide with an existing group.
    """
    import frappe

    name = base
    counter = 1

    while frappe.db.exists(GROUP_DOCTYPE, name):
        counter += 1
        name = f"{base} {counter}"

    return name


def collect():
    """Every active transition, with the tasks attached to it and the hook behind each.

    Reads the transition's task rows, not the transition's action. The two are different
    values: a transition's action is what the user clicks ("Register"), while the task it
    carries names the ``workflow_methods`` entry ("Register Correspondence"). Matching on
    the action finds nothing and reports a working setup as unconfigured.
    """
    import frappe

    hooks = hook_names()
    rows = []
    child_field = _child_fieldname() if supports_transition_tasks() else None

    for workflow in frappe.get_all(
        "Workflow",
        filters={"is_active": 1},
        fields=["name", "document_type"],
        limit_page_length=0,
    ):
        transitions = frappe.get_all(
            "Workflow Transition",
            filters={"parent": workflow.name},
            fields=["name", "action", "state", "next_state"],
            order_by="idx",
            limit_page_length=0,
        )

        for transition in transitions:
            group = None

            if supports_transition_tasks():
                group = frappe.db.get_value("Workflow Transition", transition.name, LINK_FIELD)

            tasks = []

            if group and child_field:
                tasks = frappe.get_all(
                    CHILD_DOCTYPE,
                    filters={"parent": group, "parentfield": child_field},
                    fields=["name", "task", "enabled", "asynchronous"],
                    order_by="idx",
                    limit_page_length=0,
                )

            rows.append(
                {
                    "workflow": workflow.name,
                    "doctype": workflow.document_type,
                    "transition": transition.name,
                    "action": transition.action,
                    "from": transition.state,
                    "to": transition.next_state,
                    "group": group,
                    "tasks": tasks,
                    "hooks": [task.task for task in tasks if task.task in hooks],
                }
            )

    return rows


def state_only_transitions(rows=None):
    """Transitions that change the state and run no hook.

    Not a defect: most transitions only move a document along its path. Listing them keeps
    the distinction visible between "deliberately does nothing else" and "should do
    something and does not".
    """
    return [
        f"{row['workflow']}: {row['action']} ({row['from']} -> {row['to']})"
        for row in (rows if rows is not None else collect())
        if not row["tasks"]
    ]


def unattached_hooks(rows=None):
    """Hook names that no transition task refers to, so they can never fire."""
    attached = {name for row in (rows if rows is not None else collect()) for name in row["hooks"]}
    return [name for name in hook_names() if name not in attached]


def problems(rows=None):
    """Configuration that is wrong rather than merely absent."""
    found = []

    for row in rows if rows is not None else collect():
        for task in row["tasks"]:
            label = f"{row['workflow']}: {row['action']} ({row['from']} -> {row['to']}): {task.task}"

            if task.task not in hook_names():
                found.append(f"{label}: no workflow_methods entry with this name")
            elif not task.enabled:
                found.append(f"{label}: not enabled, so it never runs")
            elif task.asynchronous:
                found.append(
                    f"{label}: 'Asynchronous' is on, so it runs outside the transition's transaction"
                )

    for name in unattached_hooks(rows if rows is not None else collect()):
        found.append(f"hook '{name}' is declared but attached to no transition")

    return found


def plan():
    """Print the transition-to-hook mapping and anything wrong with it. Changes nothing."""
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

    for row in rows:
        where = f"{row['from']} -> {row['to']}"
        print(f"{row['workflow']}: {row['action']} ({where})")

        if not row["tasks"]:
            print("    (no transition task)")
            continue

        for task in row["tasks"]:
            method = HOOK_METHODS().get(task.task)

            if method and task.enabled and not task.asynchronous:
                print(f"    ok     {task.task} -> {method.split('.')[-1]}")
            else:
                print(f"    check  {task.task} -> {method or 'no such hook'}")

    found = problems(rows)
    state_only = state_only_transitions(rows)
    print("=" * 40)

    if found:
        print(f"{len(found)} problem(s):")
        for line in found:
            print(f"  - {line}")
    else:
        print("every declared hook is attached, enabled and synchronous")

    if state_only:
        print()
        print(f"{len(state_only)} transition(s) only change the state and run no hook:")
        for line in state_only:
            print(f"  - {line}")

    return rows


def attach(workflow, transition, hook, group=None):
    """Attach one hook to one transition, explicitly.

    Automatic attachment is deliberately not offered: which transition should run which
    lifecycle method is a business decision that cannot be derived from metadata. Pass the
    three names you mean.

        bench --site <site> execute \
          murasalat_office.setup.workflow_tasks.attach \
          --kwargs "{'workflow': 'Murasalat Correspondence Workflow', \
                     'transition': 'Register', 'hook': 'Register Correspondence'}"
    """
    import frappe

    if not supports_transition_tasks():
        print("This Frappe version does not implement transition tasks; nothing to do.")
        return

    if hook not in hook_names():
        print(f"No workflow_methods entry is named '{hook}'.")
        return

    # A transition is identified by a generated name, which nobody can guess. Accept the
    # action label the user sees ("Approve") as well as the row name.
    if frappe.db.exists("Workflow Transition", transition):
        transition_doc = frappe.db.get_value(
            "Workflow Transition", transition, ["name", "parent", "action"], as_dict=True
        )
    elif workflow:
        transition_doc = frappe.db.get_value(
            "Workflow Transition",
            {"parent": workflow, "action": transition},
            ["name", "parent", "action"],
            as_dict=True,
        )
    else:
        transition_doc = None

    if not transition_doc:
        print(f"No Workflow Transition '{transition}'" + (f" in '{workflow}'." if workflow else "."))
        return

    if workflow and transition_doc.parent != workflow:
        print(f"Transition '{transition}' belongs to '{transition_doc.parent}', not '{workflow}'.")
        return

    transition = transition_doc.name

    child_field = _child_fieldname()

    if not group:
        group = frappe.db.get_value("Workflow Transition", transition, LINK_FIELD)

    if not group:
        # The doctype prompts for its name, so one has to be supplied here. Without it the
        # insert fails with "Please set the document name".
        group = unique_group_name(
            suggest_group_name(transition_doc.parent, transition_doc.get("action") or hook)
        )

        frappe.get_doc(
            {
                "doctype": GROUP_DOCTYPE,
                "name": group,
                child_field: [
                    {"doctype": CHILD_DOCTYPE, "task": hook, "enabled": 1, "asynchronous": 0}
                ],
            }
        ).insert(ignore_permissions=True)

    else:
        existing = frappe.get_all(
            CHILD_DOCTYPE,
            filters={"parent": group, "parentfield": child_field, "task": hook},
            limit_page_length=0,
        )

        if existing:
            print(f"'{hook}' is already attached to '{transition}' ({group}).")
            return

        group_doc = frappe.get_doc(GROUP_DOCTYPE, group)
        group_doc.append(child_field, {"doctype": CHILD_DOCTYPE, "task": hook, "enabled": 1, "asynchronous": 0})
        group_doc.save(ignore_permissions=True)

    if transition_doc.parent:
        workflow_doc = frappe.get_doc("Workflow", transition_doc.parent)

        for row in workflow_doc.transitions:
            if row.name == transition:
                row.set(LINK_FIELD, group)

        workflow_doc.save(ignore_permissions=True)

    frappe.db.commit()
    print(f"attached '{hook}' to '{transition}' ({group})")
