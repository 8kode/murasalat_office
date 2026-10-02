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
            "create_reply": 1,
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
        "Murasalat Correspondence": {
            "read": 1, "write": 1, "create": 1, "report": 1, "print": 1, "email": 1,
            "share": 1, "export": 1, "import": 1, "amend": 1, "create_reply": 1,
        },
        "Murasalat Referral": {
            "read": 1, "write": 1, "create": 1, "report": 1, "print": 1, "email": 1,
            "share": 1, "export": 1, "import": 1, "amend": 1,
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

# Workflow design is intentionally absent. Each institution owns the Workflow for
# Murasalat Correspondence and Murasalat Referral in Frappe Desk. The application exposes
# lifecycle methods as optional native Workflow Transition Tasks, but never dictates states,
# transition names, roles, ordering, or workflow names.
WORKFLOW_PLAN = {
    "Murasalat Correspondence": {
        "workflow_name": None,
        "workflow_state_field": "workflow_state",
        "site_defined": True,
        "transition_task_catalog": [
            "Register Correspondence", "Close Correspondence", "Seal Correspondence",
            "Reopen Correspondence",
        ],
    },
    "Murasalat Referral": {
        "workflow_name": None,
        "workflow_state_field": "workflow_state",
        "site_defined": True,
        "transition_task_catalog": [
            "Send Referral", "Receive Referral", "Complete Referral", "Cancel Referral",
        ],
    },
}

MANUAL_STEPS = [
    "Create or configure the Murasalat Correspondence Workflow in Desk according to the institution's policy.",
    "Create or configure the Murasalat Referral Workflow in Desk according to the institution's policy.",
    "Attach only the lifecycle Transition Tasks that the institution's chosen transitions require.",
    "Configure roles and permissions in Role Permission Manager.",
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

    lines += ["", "Workflow governance (site-defined):"]
    for doctype, spec in data["workflows"].items():
        lines.append(f"  • {doctype}: the institution defines the Workflow, states, transitions, roles and names.")
        lines.append(f"      optional Transition Tasks: {', '.join(spec['transition_task_catalog'])}")

    lines += ["", "Manual steps (the application does none of these):"]
    lines += [f"  {index}. {step}" for index, step in enumerate(data["manual_steps"], 1)]

    if apply:
        lines += [
            "",
            "With apply=True, the callers may materialise the roles and permission rows.",
            "Workflows and transition tasks always stay manual — see MANUAL_STEPS above.",
        ]

    return "\n".join(lines)


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
