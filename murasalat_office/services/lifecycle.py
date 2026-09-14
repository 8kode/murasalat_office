
import frappe
from frappe import _
from frappe.utils import now_datetime


def _append_activity(doc, activity_type, details=None, referral=None):
    doc.append(
        "activities",
        {
            "activity_type": activity_type,
            "activity_on": now_datetime(),
            "actor": frappe.session.user,
            "organization": (
                referral.get("recipient_organization")
                if referral and referral.get("recipient_organization")
                else doc.get("current_holder")
            ),
            "referral_number": (
                referral.get("referral_number")
                if referral
                else None
            ),
            "details": details,
        },
    )


def register_correspondence(doc):
    if doc.doctype != "Murasalat Correspondence":
        frappe.throw(
            _(
                "Register Correspondence can only run on "
                "Murasalat Correspondence."
            )
        )

    if not doc.registered_on:
        doc.registered_on = now_datetime()

        # Establish the initial organizational holder from the
        # correspondence direction. A later received referral may
        # legitimately move the holder to another Department.
        if not doc.current_holder:
            if doc.correspondence_type == "Incoming":
                doc.current_holder = doc.incoming_target_entry

            elif doc.correspondence_type == "Outgoing":
                doc.current_holder = doc.outgoing_source_entity

            elif doc.correspondence_type == "Internal":
                doc.current_holder = doc.internal_target_entry

        _append_activity(
            doc,
            "Registered",
            "Correspondence officially registered.",
        )


def close_correspondence(doc):
    if doc.doctype != "Murasalat Correspondence":
        frappe.throw(
            _(
                "Close Correspondence can only run on "
                "Murasalat Correspondence."
            )
        )

    # Represents the latest official closure.
    doc.closed_on = now_datetime()

    _append_activity(
        doc,
        "Closed",
        "Correspondence officially closed.",
    )


def seal_correspondence(doc):
    if doc.doctype != "Murasalat Correspondence":
        frappe.throw(
            _(
                "Seal Correspondence can only run on "
                "Murasalat Correspondence."
            )
        )

    if not doc.record_sealed_on:
        doc.record_sealed_on = now_datetime()
        doc.record_sealed_by = frappe.session.user

        _append_activity(
            doc,
            "Sealed",
            "Correspondence integrity snapshot sealed.",
        )


def reopen_correspondence(doc):
    if doc.doctype != "Murasalat Correspondence":
        frappe.throw(
            _(
                "Reopen Correspondence can only run on "
                "Murasalat Correspondence."
            )
        )

    doc.reopened_on = now_datetime()
    doc.reopened_by = frappe.session.user

    _append_activity(
        doc,
        "Reopened",
        "Correspondence was reopened.",
    )


def receive_referral(doc):
    if doc.doctype != "Murasalat Referral":
        frappe.throw(
            _("Receive Referral can only run on Murasalat Referral.")
        )

    if not doc.received_on:
        doc.received_on = now_datetime()
        doc.received_by = frappe.session.user

    if not doc.correspondence:
        return

    # Only a Department-targeted referral changes the
    # correspondence's organizational holder.
    if (
        doc.recipient_type != "Organization"
        or not doc.recipient_organization
    ):
        return

    correspondence = frappe.get_doc(
        "Murasalat Correspondence",
        doc.correspondence,
    )

    # Native permission boundary: receiving a referral that changes
    # the parent holder requires write permission on that parent.
    correspondence.check_permission("write")

    frappe.db.set_value(
        "Murasalat Correspondence",
        correspondence.name,
        {
            "current_holder": doc.recipient_organization,
            "current_holder_user": None,
        },
        update_modified=True,
    )


def sync_current_holder_user(doc, method=None):
    if (
        doc.reference_type != "Murasalat Correspondence"
        or not doc.reference_name
    ):
        return

    # A ToDo must never become an indirect authorization bypass.
    # The corresponding user must already have native write access
    # to the parent correspondence.
    if not frappe.db.exists(
        "Murasalat Correspondence",
        doc.reference_name,
    ):
        return

    correspondence = frappe.get_doc(
        "Murasalat Correspondence",
        doc.reference_name,
    )
    correspondence.check_permission("write")

    assignments = frappe.get_all(
        "ToDo",
        filters={
            "reference_type": "Murasalat Correspondence",
            "reference_name": doc.reference_name,
            "status": "Open",
        },
        fields=[
            "allocated_to",
            "modified",
        ],
        order_by="modified desc",
        limit_page_length=1,
    )

    current_user = (
        assignments[0].allocated_to
        if assignments
        else None
    )

    frappe.db.set_value(
        "Murasalat Correspondence",
        doc.reference_name,
        "current_holder_user",
        current_user,
        update_modified=True,
    )
    
    
def send_referral(doc):
    if doc.doctype != "Murasalat Referral":
        frappe.throw(_("Send Referral can only run on Murasalat Referral."))

    if not doc.correspondence:
        frappe.throw(
            _("A referral must be linked to a Correspondence before it can be sent.")
        )

    if not doc.recipient_type:
        frappe.throw(
            _("Recipient Type is required before sending the referral.")
        )

    if doc.recipient_type == "Organization":
        if not doc.recipient_organization:
            frappe.throw(
                _("Recipient Department is required before sending the referral.")
            )

    if doc.recipient_type == "User":
        if not doc.recipient_user:
            frappe.throw(
                _("Recipient User is required before sending the referral.")
            )

    if not doc.sent_on:
        doc.sent_on = now_datetime()
        
        
def complete_referral(doc):
    if doc.doctype != "Murasalat Referral":
        frappe.throw(
            _("Complete Referral can only run on Murasalat Referral.")
        )

    if not doc.received_on:
        frappe.throw(
            _("A referral must be received before it can be completed.")
        )

    if not doc.completed_on:
        doc.completed_on = now_datetime()
        doc.completed_by = frappe.session.user        