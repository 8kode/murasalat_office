"""Recording and withdrawing the approval decision.

The Approval Request's ``approved_by``/``approved_on`` fields are read-only in the DocType,
which means nothing in the Desk UI can write them. Without a workflow task that stamps
them, they stay empty forever and the request never records who approved it — the "Approve"
transition would change the state and leave no decision behind.

These two methods are the writers. They are registered as ``workflow_methods`` and attached
to the Approval Workflow transitions, so the decision is stamped at the moment of approval
and withdrawn when the request is returned for amendment.

``MurasalatApprovalRequest._freeze_decision`` is the guard that makes them trustworthy:
it refuses a stamp naming anyone but the acting user and refuses any rewrite of a recorded
decision. The stamp is written here; the guard decides whether it may be.
"""
import frappe
from frappe import _
from frappe.utils import now_datetime

APPROVAL_DOCTYPE = "Murasalat Approval Request"


def stamp_approval(doc):
    """Record the approval decision, once, when the workflow reaches Approved."""
    if doc.doctype != APPROVAL_DOCTYPE:
        frappe.throw(
            _("Stamp Approval can only run on Murasalat Approval Request.")
        )

    if doc.get("approved_by"):
        return

    doc.approved_by = frappe.session.user
    doc.approved_on = now_datetime()


def clear_approval(doc):
    """Withdraw the decision when the request is sent back for amendment.

    Returning a request for amendment retracts the approval, so the record must stop
    claiming one. The earlier decision is not lost: Frappe's own Version history keeps it
    because the document tracks changes.
    """
    if doc.doctype != APPROVAL_DOCTYPE:
        frappe.throw(
            _("Clear Approval can only run on Murasalat Approval Request.")
        )

    if not doc.get("approved_by") and not doc.get("approved_on"):
        return

    doc.approved_by = None
    doc.approved_on = None
