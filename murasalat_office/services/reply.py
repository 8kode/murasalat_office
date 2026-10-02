import frappe
from frappe import _

from murasalat_office.services.lifecycle import OPEN_REFERRAL_FILTERS

CORRESPONDENCE = "Murasalat Correspondence"
REFERRAL = "Murasalat Referral"
REPLY_TO = "Reply To"


def _get_correspondence(name, permission_type="read"):
    if not name:
        frappe.throw(_("Correspondence is required."))
    doc = frappe.get_doc(CORRESPONDENCE, name)
    doc.check_permission(permission_type)
    return doc


def _check_create_reply_permission(doc):
    if not frappe.has_permission(doc, ptype="create_reply"):
        frappe.throw(
            _("You do not have permission to create a reply for this correspondence."),
            frappe.PermissionError,
        )
    if not frappe.has_permission(CORRESPONDENCE, ptype="create"):
        frappe.throw(
            _("You do not have permission to create Murasalat Correspondence records."),
            frappe.PermissionError,
        )


def _get_open_referrals(name):
    return frappe.get_all(
        REFERRAL,
        filters=[["correspondence", "=", name], *OPEN_REFERRAL_FILTERS],
        fields=["name", "referral_number", "recipient_type", "recipient_department", "recipient_user", "due_date"],
        order_by="due_date asc, modified desc",
        limit_page_length=0,
    )


def _validate_reply_source(incoming):
    if incoming.correspondence_direction != "Incoming":
        frappe.throw(_("Only an Incoming correspondence can be replied to."))
    if not incoming.registered_on:
        frappe.throw(_("The incoming correspondence must be registered before a reply can be created."))
    if incoming.closed_on:
        frappe.throw(_("A reply cannot be created because the incoming correspondence is closed."))
    if incoming.record_sealed_on:
        frappe.throw(_("A reply cannot be created from a sealed incoming correspondence."))
    if not incoming.incoming_source_entity:
        frappe.throw(_("The incoming correspondence has no external sender."))
    if not incoming.incoming_target_entry:
        frappe.throw(_("The incoming correspondence has no receiving department."))


def _ensure_no_open_referrals(incoming):
    open_referrals = _get_open_referrals(incoming.name)
    if open_referrals:
        frappe.throw(
            _("A reply cannot be created while {0} referral(s) are still open. Complete or cancel all sent referrals first.").format(len(open_referrals))
        )


def get_reply_context(correspondence):
    incoming = _get_correspondence(correspondence, "read")
    open_referrals = _get_open_referrals(incoming.name)
    blockers = []
    if incoming.correspondence_direction != "Incoming":
        blockers.append(_("Only Incoming correspondence can receive an official reply."))
    if not incoming.registered_on:
        blockers.append(_("The correspondence must be registered first."))
    if incoming.closed_on:
        blockers.append(_("The correspondence is already closed."))
    if incoming.record_sealed_on:
        blockers.append(_("The correspondence is sealed."))
    if open_referrals:
        blockers.append(_("There are {0} open referral(s). Complete or cancel them first.").format(len(open_referrals)))
    if not incoming.incoming_source_entity:
        blockers.append(_("The incoming correspondence has no external sender."))
    if not incoming.incoming_target_entry:
        blockers.append(_("The incoming correspondence has no receiving department."))
    try:
        _check_create_reply_permission(incoming)
    except frappe.PermissionError as exc:
        blockers.append(str(exc) or _("You do not have permission to create a reply for this correspondence."))

    referrals = frappe.get_list(
        REFERRAL,
        filters={"correspondence": incoming.name},
        fields=[
            "name", "referral_number", "recipient_type", "recipient_department", "recipient_user",
            "due_date", "sent_on", "received_on", "completed_on", "cancelled_on",
            "cancel_reason", "completion_result", "private_referral",
        ],
        order_by="creation asc",
        limit_page_length=0,
    )

    attachments = [
        {"name": row.name, "file": row.file, "attachment_type": row.attachment_type,
         "is_secret": row.is_secret, "file_hash": row.file_hash}
        for row in (incoming.attachments or [])
    ]

    return {
        "incoming": {
            "name": incoming.name, "subject": incoming.subject,
            "sender": incoming.incoming_source_entity,
            "receiving_department": incoming.incoming_target_entry,
            "external_letter_number": incoming.external_letter_number,
            "external_letter_date": incoming.external_letter_date,
            "due_date": incoming.due_date, "notes": incoming.notes,
        },
        "referrals": referrals, "attachments": attachments,
        "open_referral_count": len(open_referrals),
        "can_create_reply": not blockers, "blockers": blockers,
        "default_source_department": incoming.incoming_target_entry,
        "default_target_external_party": incoming.incoming_source_entity,
    }


def create_reply_draft(
    correspondence, subject=None, notes=None, source_department=None, salutation=None,
    closing_phrase=None, signatory_name=None, signatory_position=None, approval_entity=None,
    preparation_entity=None, prepared_on=None,
):
    incoming = _get_correspondence(correspondence, "read")
    _check_create_reply_permission(incoming)
    _validate_reply_source(incoming)
    _ensure_no_open_referrals(incoming)

    source_department = source_department or incoming.incoming_target_entry
    if source_department != incoming.incoming_target_entry:
        frappe.throw(_("The reply must be issued from the department that received the incoming correspondence."))

    reply = frappe.new_doc(CORRESPONDENCE)
    reply.subject = subject or _("Reply: {0}").format(incoming.subject)
    reply.correspondence_direction = "Outgoing"
    reply.transaction_type = incoming.transaction_type
    reply.confidentiality = incoming.confidentiality
    reply.importance = incoming.importance
    reply.outgoing_source_entity = source_department
    reply.outgoing_target_entry = incoming.incoming_source_entity
    reply.notes = notes or ""
    reply.salutation = salutation or "السادة/"
    reply.closing_phrase = closing_phrase or "وتفضلوا بقبول خالص التحية والتقدير"
    reply.signatory_name = signatory_name or ""
    reply.signatory_position = signatory_position or ""
    reply.approval_entity = approval_entity or ""
    reply.preparation_entity = preparation_entity or source_department
    reply.prepared_on = prepared_on or frappe.utils.today()

    link = reply.append("links", {})
    link.linked_correspondence = incoming.name
    link.relationship_type = REPLY_TO
    link.link_order = 1

    reply.insert()
    return {
        "name": reply.name, "doctype": reply.doctype, "url": reply.get_url(),
        "source_correspondence": incoming.name, "subject": reply.subject,
    }
