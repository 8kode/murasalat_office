from __future__ import annotations

import frappe


WORKFLOW_NAME = "Murasalat Correspondence Workflow"

WORKFLOW_STATES = [
    {
        "name": "Murasalat Draft",
        "style": "Warning",
    },
    {
        "name": "Murasalat Registered",
        "style": "Primary",
    },
    {
        "name": "Murasalat Closed",
        "style": "Success",
    },
    {
        "name": "Murasalat Cancelled",
        "style": "Danger",
    },
]

WORKFLOW_ACTIONS = [
    "Register",
    "Close",
    "Reopen",
    "Cancel",
]


def install_workflow():
    create_states()
    create_actions()

    if frappe.db.exists("Workflow", WORKFLOW_NAME):
        return frappe.get_doc("Workflow", WORKFLOW_NAME)

    workflow = frappe.get_doc(
        {
            "doctype": "Workflow",
            "workflow_name": WORKFLOW_NAME,
            "document_type": "Murasalat Correspondence",
            "is_active": 1,
            "override_status": 0,
            "send_email_alert": 0,
            "enable_action_confirmation": 1,
            "workflow_state_field": "workflow_state",
            "states": [
                {
                    "state": "Murasalat Draft",
                    "doc_status": "0",
                    "allow_edit": "Murasalat Clerk",
                    "send_email": 0,
                },
                {
                    "state": "Murasalat Registered",
                    "doc_status": "1",
                    "allow_edit": "Murasalat Manager",
                    "send_email": 0,
                },
                {
                    "state": "Murasalat Closed",
                    "doc_status": "1",
                    "allow_edit": "Murasalat Manager",
                    "send_email": 0,
                },
                {
                    "state": "Murasalat Cancelled",
                    "doc_status": "2",
                    "allow_edit": "Murasalat Manager",
                    "send_email": 0,
                },
            ],
            "transitions": [
                {
                    "state": "Murasalat Draft",
                    "action": "Register",
                    "next_state": "Murasalat Registered",
                    "allowed": "Murasalat Clerk",
                    "allow_self_approval": 1,
                },
                {
                    "state": "Murasalat Registered",
                    "action": "Close",
                    "next_state": "Murasalat Closed",
                    "allowed": "Murasalat Manager",
                    "allow_self_approval": 1,
                    "condition": "doc.pending_referral_count == 0",
                },
                {
                    "state": "Murasalat Closed",
                    "action": "Reopen",
                    "next_state": "Murasalat Registered",
                    "allowed": "Murasalat Manager",
                    "allow_self_approval": 1,
                },
                {
                    "state": "Murasalat Registered",
                    "action": "Cancel",
                    "next_state": "Murasalat Cancelled",
                    "allowed": "Murasalat Manager",
                    "allow_self_approval": 1,
                    "condition": "doc.pending_referral_count == 0",
                },
            ],
        }
    )

    workflow.insert(ignore_permissions=True)

    return workflow


def create_states():
    for state in WORKFLOW_STATES:
        if frappe.db.exists("Workflow State", state["name"]):
            continue

        frappe.get_doc(
            {
                "doctype": "Workflow State",
                "workflow_state_name": state["name"],
                "style": state["style"],
            }
        ).insert(ignore_permissions=True)


def create_actions():
    for action in WORKFLOW_ACTIONS:
        if frappe.db.exists("Workflow Action Master", action):
            continue

        frappe.get_doc(
            {
                "doctype": "Workflow Action Master",
                "workflow_action_name": action,
            }
        ).insert(ignore_permissions=True)