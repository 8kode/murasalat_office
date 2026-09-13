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
            _("Register Correspondence can only run on Murasalat Correspondence.")
        )

    if not doc.registered_on:
        doc.registered_on = now_datetime()

        _append_activity(
            doc,
            "Registered",
            "Correspondence officially registered.",
        )


def close_correspondence(doc):
    if doc.doctype != "Murasalat Correspondence":
        frappe.throw(
            _("Close Correspondence can only run on Murasalat Correspondence.")
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
            _("Seal Correspondence can only run on Murasalat Correspondence.")
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
            _("Reopen Correspondence can only run on Murasalat Correspondence.")
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

    # Only a Department-targeted referral changes the correspondence's
    # department holder.
    if (
        doc.recipient_type != "Organization"
        or not doc.recipient_organization
    ):
        return

    correspondence = frappe.get_doc(
        "Murasalat Correspondence",
        doc.correspondence,
    )

    # The user executing Receive must also have native write permission
    # on the parent correspondence because this transition changes its
    # operational holder.
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

    if not frappe.db.exists(
        "Murasalat Correspondence",
        doc.reference_name,
    ):
        return

    frappe.db.set_value(
        "Murasalat Correspondence",
        doc.reference_name,
        "current_holder_user",
        current_user,
        update_modified=True,
    )