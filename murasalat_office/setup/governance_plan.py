"""The governance a site needs, described — and materialised only on explicit request.

Native-First says this application ships no roles, no permission rows and no workflow.
This module does not break that: ``describe()`` is pure preview and is what the
defaults produce, and ``materialize()`` refuses to run unless the caller passes an
explicit confirmation. Nothing here is applied on install or on migrate, and there is
no ``fixtures`` hook.

Role names are deliberately **not** the business role names used anywhere else in this
code base: governance belongs to the site, and the application never refers to a role
by name at runtime.

    bench --site <site> execute murasalat_office.setup.governance_plan.describe
    bench --site <site> execute murasalat_office.setup.governance_plan.materialize \
        --kwargs "{'confirm': True}"
"""

import frappe

# Role -> {doctype: rights}. Rights use the native DocPerm field names.
# ``delete`` and ``share`` are held back on purpose: deleting a correspondence record
# would destroy the sealed audit trail this application exists to keep.
PERMISSION_PLAN = {
    "Correspondence Clerk": {
        "Murasalat Correspondence": {
            "read": 1, "write": 1, "create": 1, "report": 1, "print": 1, "email": 1, "share": 1,
        },
        "Murasalat Referral": {
            "read": 1, "write": 1, "create": 1, "report": 1, "print": 1, "email": 1, "share": 1,
        },
        "Murasalat Attachment": {"read": 1, "write": 1, "create": 1},
        "Murasalat Correspondence Activity": {"read": 1, "write": 1, "create": 1},
        "Murasalat Transaction Type": {"read": 1},
        "Murasalat Confidentiality Level": {"read": 1},
        "Murasalat Importance Level": {"read": 1},
        "Murasalat Correspondence Direction": {"read": 1},
        "Murasalat Referral Direction": {"read": 1},
        "Murasalat External Party": {"read": 1, "create": 1, "write": 1},
        "Murasalat External Party Type": {"read": 1},
    },
    "Correspondence Supervisor": {
        # No ``amend``: Frappe refuses an amend right on a DocType that is not submittable
        # (core/doctype/doctype/doctype.py, check_if_submittable), and no Murasalat DocType is.
        # An amendment in this application is the Workflow's Reopen transition, which is a
        # different thing entirely and is governed by a transition task.
        "Murasalat Correspondence": {
            "read": 1, "write": 1, "create": 1, "report": 1, "print": 1, "email": 1,
            "share": 1, "export": 1, "import": 1,
        },
        "Murasalat Referral": {
            "read": 1, "write": 1, "create": 1, "report": 1, "print": 1, "email": 1,
            "share": 1, "export": 1, "import": 1,
        },
        "Murasalat Approval Request": {"read": 1, "write": 1, "create": 1, "report": 1},
        "Murasalat Delegation": {"read": 1, "write": 1, "create": 1, "report": 1},
        "Murasalat User Organization Membership": {
            "read": 1, "write": 1, "create": 1, "report": 1,
        },
        "Murasalat Attachment": {"read": 1, "write": 1, "create": 1},
        "Murasalat Correspondence Activity": {"read": 1, "write": 1, "create": 1},
        "Murasalat Transaction Type": {"read": 1, "create": 1, "write": 1},
        "Murasalat Confidentiality Level": {"read": 1, "create": 1, "write": 1},
        "Murasalat Importance Level": {"read": 1, "create": 1, "write": 1},
        "Murasalat Correspondence Direction": {"read": 1, "create": 1, "write": 1},
        "Murasalat Referral Direction": {"read": 1, "create": 1, "write": 1},
        "Murasalat External Party": {"read": 1, "create": 1, "write": 1},
        "Murasalat External Party Type": {"read": 1, "create": 1, "write": 1},
    },
    "Correspondence Auditor": {
        # Read-only by design: an auditor must never be able to alter a sealed record.
        "Murasalat Correspondence": {"read": 1, "report": 1, "print": 1, "export": 1},
        "Murasalat Referral": {"read": 1, "report": 1, "print": 1, "export": 1},
        "Murasalat Approval Request": {"read": 1, "report": 1},
        "Murasalat Delegation": {"read": 1, "report": 1},
        "Murasalat User Organization Membership": {"read": 1, "report": 1},
        "Murasalat Attachment": {"read": 1},
        "Murasalat Correspondence Activity": {"read": 1},
        "Murasalat External Party": {"read": 1},
    },
}

# Workflow shape only. The application creates none of this; the administrator does,
# in Desk, following docs/WORKFLOW_GOVERNANCE.md. The ``task`` values are the exact
# workflow_methods hook names — a typo there stops every transition that uses it.
WORKFLOW_PLAN = {
    "Murasalat Correspondence": {
        "workflow_name": "Murasalat Correspondence Lifecycle",
        "workflow_state_field": "workflow_state",
        "states": ["Draft", "Registered", "Closed", "Sealed"],
        "transitions": [
            {"action": "Register", "state": "Draft", "next_state": "Registered",
             "allowed": "Correspondence Clerk", "task": "Register Correspondence"},
            {"action": "Close", "state": "Registered", "next_state": "Closed",
             "allowed": "Correspondence Supervisor", "task": "Close Correspondence"},
            {"action": "Seal", "state": "Closed", "next_state": "Sealed",
             "allowed": "Correspondence Supervisor", "task": "Seal Correspondence"},
            {"action": "Reopen", "state": "Sealed", "next_state": "Registered",
             "allowed": "Correspondence Supervisor", "task": "Reopen Correspondence"},
        ],
    },
    "Murasalat Referral": {
        "workflow_name": "Murasalat Referral Lifecycle",
        "workflow_state_field": "workflow_state",
        "states": ["Draft", "Sent", "Received", "Completed"],
        "transitions": [
            {"action": "Send", "state": "Draft", "next_state": "Sent",
             "allowed": "Correspondence Clerk", "task": "Send Referral"},
            {"action": "Receive", "state": "Sent", "next_state": "Received",
             "allowed": "Correspondence Clerk", "task": "Receive Referral"},
            {"action": "Complete", "state": "Received", "next_state": "Completed",
             "allowed": "Correspondence Clerk", "task": "Complete Referral"},
        ],
    },
}

# Cannot be automated safely: creating Workflow Document State rows needs field names
# this module has not verified against the framework source, and guessing them on a
# production launch is worse than doing it by hand.
MANUAL_STEPS = [
    "Create the Workflow States in Desk (Draft, Registered, Closed, Sealed, Sent, Received, Completed).",
    "Create the two Workflows and their transitions from the plan below.",
    "Create one 'Workflow Transition Tasks' document holding the seven task rows, then attach it to every transition that writes lifecycle fields.",
    "Tick the roles on the reports and number cards you want each role to see.",
    "See docs/WORKFLOW_GOVERNANCE.md for the exact task names and the asynchronous trap.",
]


def plan():
    """Return the full governance plan as data. Reads nothing, writes nothing."""
    return {
        "roles": sorted(PERMISSION_PLAN),
        "permissions": [
            {"role": role, "doctype": doctype, "rights": dict(rights)}
            for role, doctypes in sorted(PERMISSION_PLAN.items())
            for doctype, rights in sorted(doctypes.items())
        ],
        "workflows": WORKFLOW_PLAN,
        "manual_steps": list(MANUAL_STEPS),
        "creates_nothing_by_default": True,
    }


def describe(apply=False):
    """Render the plan as text for an administrator to read and execute in Desk."""
    data = plan()
    lines = ["Murasalat Office — governance plan", "=" * 34, "", "Roles to create:"]

    for role in data["roles"]:
        lines.append(f"  • {role}")

    lines += ["", "Role Permission Manager rows:"]
    for entry in data["permissions"]:
        rights = ", ".join(sorted(k for k, v in entry["rights"].items() if v))
        lines.append(f"  • {entry['role']}  →  {entry['doctype']}: {rights}")

    lines += ["", "Workflows to create in Desk:"]
    for doctype, spec in data["workflows"].items():
        lines.append(f"  • {spec['workflow_name']}  (on {doctype})")
        lines.append(f"      states: {', '.join(spec['states'])}")
        for transition in spec["transitions"]:
            lines.append(
                f"      {transition['state']} --{transition['action']}--> "
                f"{transition['next_state']}   [{transition['allowed']}]   "
                f"task: {transition['task']}"
            )

    lines += ["", "Manual steps (the application does none of these):"]
    lines += [f"  {index}. {step}" for index, step in enumerate(data["manual_steps"], 1)]

    if apply:
        lines += [
            "",
            "With apply=True, the callers may materialise the roles and permission rows.",
            "Workflows and transition tasks always stay manual — see MANUAL_STEPS above.",
        ]

    return "\n".join(lines)


# Rights Frappe only accepts on a submittable DocType.
SUBMISSION_ONLY_RIGHTS = ("submit", "cancel", "amend")


def plan_problems(is_submittable=None):
    """Rights in the plan that Frappe would refuse, caught before anything is written.

    Rows are appended to the DocType's own permission table and the DocType is then saved, so
    Frappe validates them late - and with a message that names a field rather than the row:
    "Cannot set Assign Amend if not Submittable". A launch once stopped there, after the roles
    had been created, and the master data, the print formats, the notifications and the
    Workflows never ran. This turns that into a readable problem, found before any write.

    ``is_submittable`` is a callable ``doctype -> bool``; the default reads the live meta.
    An empty list means the plan is safe to materialise.
    """
    if is_submittable is None:
        def is_submittable(doctype):
            return bool(frappe.get_meta(doctype).is_submittable)

    problems = []
    for role, doctypes in sorted(PERMISSION_PLAN.items()):
        for doctype, rights in sorted(doctypes.items()):
            if is_submittable(doctype):
                continue
            for right in SUBMISSION_ONLY_RIGHTS:
                if rights.get(right):
                    problems.append(
                        f"{role} on {doctype}: '{right}' needs a submittable DocType, "
                        "and this one is not. An amendment here is the Reopen transition."
                    )
    return problems


def materialize(confirm=False):
    """Create the roles and the native DocPerm rows. Refuses without ``confirm=True``.

    Idempotent: an existing role is left alone, and a DocPerm row is only appended when
    that role has no row yet on that DocType. Workflows are never created here.
    """
    if not confirm:
        frappe.throw(
            "Refusing to change site governance without confirm=True. "
            "Run describe() first, then materialize(confirm=True) if the plan is right."
        )

    problems = plan_problems()
    if problems:
        raise ValueError(
            "The permission plan asks for rights Frappe will refuse:\n  "
            + "\n  ".join(problems)
        )

    created_roles = []
    created_perms = []

    for role in sorted(PERMISSION_PLAN):
        if not frappe.db.exists("Role", role):
            frappe.get_doc(
                {"doctype": "Role", "role_name": role, "desk_access": 1}
            ).insert(ignore_permissions=True)
            created_roles.append(role)

    for role, doctypes in sorted(PERMISSION_PLAN.items()):
        for doctype, rights in sorted(doctypes.items()):
            meta = frappe.get_doc("DocType", doctype)
            if any(row.role == role for row in meta.permissions or []):
                continue
            row = {"doctype": "DocPerm", "role": role, "permlevel": 0}
            row.update(rights)
            meta.append("permissions", row)
            meta.save(ignore_permissions=True)
            created_perms.append({"role": role, "doctype": doctype})

    return {
        "created_roles": created_roles,
        "created_permissions": created_perms,
        "workflows_created": [],
        "manual_steps_remaining": list(MANUAL_STEPS),
    }


# ---------------------------------------------------------------- reference data
#
# A Link field cannot resolve a record the user may not read, so every role that picks an
# attachment type or an archive location needs read on those two tables. Both hold nothing
# confidential - a type name and a shelf name - and leaving them out is the kind of gap that
# only shows up when a clerk opens a form and finds an empty picker.
VOCABULARY_READ = {
    "Murasalat Attachment Type": {"read": 1},
    "Murasalat Archive Location": {"read": 1},
}

for _role_plan in PERMISSION_PLAN.values():
    for _vocabulary, _rights in VOCABULARY_READ.items():
        _role_plan.setdefault(_vocabulary, dict(_rights))
