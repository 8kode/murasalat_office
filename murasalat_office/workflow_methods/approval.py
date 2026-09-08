import frappe
from frappe.utils import now_datetime


def mark_under_approval(doc):
    _sync(doc, "Under Approval", "Approval Submitted", "Approval request moved to formal approval.")


def mark_approved(doc):
    doc.db_set("approved_by", frappe.session.user, update_modified=False)
    doc.db_set("approved_on", now_datetime(), update_modified=False)
    _sync(doc, "Approved", "Approval Granted", "Correspondence approved through the formal workflow.")


def mark_returned(doc):
    _sync(doc, "Under Review", "Approval Returned", "Approval request returned for amendment.")


def mark_rejected(doc):
    _sync(doc, "Rejected", "Approval Rejected", "Approval request rejected through the formal workflow.")


def _sync(doc, status, activity_type, details):
    correspondence = frappe.get_doc("Murasalat Correspondence", doc.correspondence)
    correspondence.status = status
    correspondence.append("activities", {
        "activity_type": activity_type,
        "activity_on": now_datetime(),
        "actor": frappe.session.user,
        "details": details + (f" | Approval Request: {doc.name}" if doc.name else ""),
    })
    correspondence.flags.murasalat_approval_sync = True
    correspondence.save(ignore_permissions=True)
