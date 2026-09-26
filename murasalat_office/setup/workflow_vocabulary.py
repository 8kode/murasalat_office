"""The two vocabularies a Workflow depends on, for a small correspondence office.

A Workflow is not self-contained. Frappe resolves it against two tables of names, and on a fresh
site neither existed:

* ``Workflow Document State.state`` is a Link to **Workflow State**, and ``workflow.py`` throws
  "<state> not a valid State" for one that is not there.
* ``Workflow Transition.action`` is a Link to **Workflow Action Master**, so a transition whose
  action is not a record cannot be saved at all.

Both are pure vocabulary: a name, and for a state an icon and a colour that the Desk shows as the
status pill. They live here in one place. The names are derived from ``provision.WORKFLOWS`` - that
module owns the shape of the lifecycle and passes the names in - so this list and the Workflows can
never drift apart.

What a small office gets from the appearance below, in one screenful:

* grey-teal through green: a record moves from work-in-progress to done;
* amber for the two states that are waiting on someone else (Closed, Pending Approval);
* red only for Cancelled.

Creation is idempotent and additive. An existing Workflow State is left alone - an administrator may
have restyled it in Desk - and only appearance fields that are empty are filled in. Nothing is ever
deleted or renamed: a rename would break the notification conditions and every Workflow transition
that names the state.

Fieldnames come from the live meta rather than the docstring of a release, so a renamed framework
field surfaces as one clear message instead of a half-created record.
"""
import frappe
from frappe import _

# Read from frappe/frappe/workflow/doctype/workflow_state/workflow_state.json, version 16.
# A wrong value is refused by the Select, so the two closed sets are pinned here.
STATE_STYLES = ("Primary", "Info", "Success", "Warning", "Danger", "Inverse")

# icon -> the state it marks, chosen from the framework's own icon Select.
STATE_APPEARANCE = {
    "Draft": {"icon": "edit", "style": "Inverse"},
    "Registered": {"icon": "inbox", "style": "Info"},
    "Closed": {"icon": "lock", "style": "Warning"},
    "Sealed": {"icon": "ok-sign", "style": "Success"},
    "Sent": {"icon": "share", "style": "Info"},
    "Received": {"icon": "download", "style": "Primary"},
    "Completed": {"icon": "ok", "style": "Success"},
    "Cancelled": {"icon": "ban-circle", "style": "Danger"},
    "Pending Approval": {"icon": "time", "style": "Warning"},
    "Approved": {"icon": "ok-circle", "style": "Success"},
}

DEFAULT_APPEARANCE = {"icon": "circle-arrow-right", "style": "Primary"}

WORKFLOW_STATE = "Workflow State"
WORKFLOW_ACTION = "Workflow Action Master"


def appearance(state):
    """The icon and colour for a state, with a readable default for a name added later."""
    return dict(STATE_APPEARANCE.get(state, DEFAULT_APPEARANCE))


def _field(meta, *candidates):
    """The first of these fieldnames the live meta declares."""
    for candidate in candidates:
        if meta.get_field(candidate):
            return candidate

    available = sorted(field.fieldname for field in meta.fields)
    frappe.throw(
        _("None of {0} exists on {1}. Available fields: {2}").format(
            ", ".join(candidates), meta.name, ", ".join(available)
        )
    )


def ensure_states(states):
    """Create the Workflow States that do not exist yet, and style the ones that are bare.

    Returns ``{"created": [...], "styled": [...], "existing": [...]}``.
    """
    meta = frappe.get_meta(WORKFLOW_STATE)
    name_field = _field(meta, "workflow_state_name", "state")
    icon_field = meta.get_field("icon")
    style_field = meta.get_field("style")

    created, styled, existing = [], [], []

    for state in states:
        wanted = appearance(state)

        if not frappe.db.exists(WORKFLOW_STATE, state):
            record = {"doctype": WORKFLOW_STATE, name_field: state}
            if icon_field:
                record["icon"] = wanted["icon"]
            if style_field:
                record["style"] = wanted["style"]
            frappe.get_doc(record).insert(ignore_permissions=True)
            created.append(state)
            continue

        # Existing: fill only what is empty. A value an administrator chose in Desk stays.
        document = frappe.get_doc(WORKFLOW_STATE, state)
        missing = {}
        if icon_field and not document.get("icon"):
            missing["icon"] = wanted["icon"]
        if style_field and not document.get("style"):
            missing["style"] = wanted["style"]

        if missing:
            frappe.db.set_value(WORKFLOW_STATE, state, missing)
            styled.append(state)
        else:
            existing.append(state)

    return {"created": created, "styled": styled, "existing": existing}


def ensure_actions(actions):
    """Create the Workflow Action Masters a transition names, so the Link resolves.

    ``Workflow Transition.action`` is a Link. Frappe validates links on save, so a Workflow whose
    transition names an action that is not a record here cannot be inserted at all - the failure
    this module exists to prevent.

    Returns ``{"created": [...], "existing": [...]}``.
    """
    meta = frappe.get_meta(WORKFLOW_ACTION)
    name_field = _field(meta, "workflow_action_name", "action")

    created, existing = [], []

    for action in actions:
        if frappe.db.exists(WORKFLOW_ACTION, action):
            existing.append(action)
            continue
        frappe.get_doc({"doctype": WORKFLOW_ACTION, name_field: action}).insert(
            ignore_permissions=True
        )
        created.append(action)

    return {"created": created, "existing": existing}


def plan(states, actions):
    """Read-only: which names exist and which are missing. Writes nothing."""
    return {
        "states": {
            name: {"exists": bool(frappe.db.exists(WORKFLOW_STATE, name)),
                   "appearance": appearance(name)}
            for name in states
        },
        "actions": {
            name: {"exists": bool(frappe.db.exists(WORKFLOW_ACTION, name))}
            for name in actions
        },
    }
