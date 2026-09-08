import frappe
from frappe import _
from frappe.utils import now_datetime


def _errors(doc):
    errors = []
    if not doc.subject:
        errors.append(_("Subject is required."))
    if not doc.transaction_type:
        errors.append(_("Transaction Type is required."))
    if not doc.confidentiality:
        errors.append(_("Confidentiality is required."))
    if not doc.importance:
        errors.append(_("Importance is required."))

    if doc.correspondence_type == "Incoming":
        if not doc.source_entity:
            errors.append(_("Incoming correspondence requires Incoming From."))
        if not doc.external_letter_number:
            errors.append(_("Incoming correspondence requires External Letter Number."))
        if not doc.external_letter_date:
            errors.append(_("Incoming correspondence requires External Letter Date."))
    elif doc.correspondence_type == "Outgoing":
        if not doc.target_entity:
            errors.append(_("Outgoing correspondence requires Target Entity."))
    elif doc.correspondence_type == "Internal":
        if not doc.target_entity and not (doc.referrals or []):
            errors.append(_("Internal correspondence requires a Target Entity or at least one Referral."))

    if not doc.attachments:
        errors.append(_("At least one attachment is required before registration."))
    elif not any(r.attachment_type == "Main Letter" for r in doc.attachments):
        errors.append(_("A Main Letter attachment is required before registration."))

    return errors


def validate_registration_ready(doc):
    return _errors(doc)


def register(doc):
    if doc.status not in {"Draft", "Reopened"}:
        frappe.throw(_("Only Draft or Reopened correspondence can be registered."))
    errors = _errors(doc)
    if errors:
        frappe.throw("<br>".join(errors), title=_("Registration Checklist"))
    doc.status = "Registered"
    doc.save()
    return doc


def send(doc):
    if doc.status not in {"Registered", "Reopened"}:
        frappe.throw(_("Correspondence must be registered before sending."))
    if not doc.referrals:
        frappe.throw(_("At least one referral is required before sending."))
    active = 0
    for row in doc.referrals:
        if row.status in {"Pending", "Draft", None, ""}:
            row.status = "Sent"
            row.sent_on = now_datetime()
            active += 1
    if not active and not any(r.status in {"Sent", "Received", "In Progress", "Overdue"} for r in doc.referrals):
        frappe.throw(_("No referral is available to send."))
    doc.status = "Sent"
    doc.save()
    return doc
