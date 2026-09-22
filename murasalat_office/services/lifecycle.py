import frappe
from frappe import _
from frappe.utils import now_datetime


OPEN_REFERRAL_FILTERS = [
    ["sent_on", "is", "set"],
    ["completed_on", "is", "not set"],
]


def _append_activity(doc, activity_type, details=None, referral=None):
    """Append an activity to the current document.

    This operates on the in-memory document and therefore participates in
    the normal save/Workflow transaction of the document invoking the
    lifecycle method.
    """
    doc.append(
        "activities",
        {
            "activity_type": activity_type,
            "activity_on": now_datetime(),
            "actor": frappe.session.user,
            "organization": (
                referral.get("recipient_department")
                if referral and referral.get("recipient_department")
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


def _append_referral_activity(referral, activity_type, details):
    """Record a Referral lifecycle event on its parent Correspondence.

    The parent must be writable by the actor because this is a real child-table
    mutation. This intentionally uses the normal ORM rather than a database
    bypass, preserving Frappe validation/permission behavior.
    """
    if not referral.get("correspondence"):
        return

    correspondence = frappe.get_doc(
        "Murasalat Correspondence",
        referral.correspondence,
    )

    correspondence.check_permission("write")

    _append_activity(
        correspondence,
        activity_type,
        details=details,
        referral=referral,
    )

    correspondence.save()


def _get_open_referrals(correspondence_name):
    """Return open referrals regardless of report/list permissions.

    This is a domain invariant used when closing a Correspondence. It is not
    a data-exposure API and therefore does not use a permission-aware list.
    """
    return frappe.get_all(
        "Murasalat Referral",
        filters={
            "correspondence": correspondence_name,
            **OPEN_REFERRAL_FILTERS,
        },
        fields=["name"],
        order_by="due_date asc, modified desc",
        limit_page_length=0,
    )


def register_correspondence(doc):
    if doc.doctype != "Murasalat Correspondence":
        frappe.throw(
            _(
                "Register Correspondence can only run on "
                "Murasalat Correspondence."
            )
        )

    if doc.registered_on:
        return

    direction = doc.correspondence_direction

    holder_by_direction = {
        "Incoming": doc.incoming_target_entry,
        "Outgoing": doc.outgoing_source_entity,
        "Internal": doc.internal_target_entry,
    }

    if direction not in holder_by_direction:
        frappe.throw(
            _(
                "A valid Correspondence Direction is required before registration."
            )
        )

    initial_holder = holder_by_direction[direction]

    if not initial_holder:
        frappe.throw(
            _(
                "The organizational holder cannot be empty when correspondence "
                "is registered."
            )
        )

    doc.registered_on = now_datetime()
    doc.current_holder = initial_holder

    # current_holder_user is retained only as a legacy/deprecated projection
    # during migration. It is not populated from ToDo anymore.
    if hasattr(doc, "current_holder_user"):
        doc.current_holder_user = None

    _append_activity(
        doc,
        "Registered",
        _("Correspondence officially registered."),
    )


def close_correspondence(doc):
    if doc.doctype != "Murasalat Correspondence":
        frappe.throw(
            _(
                "Close Correspondence can only run on "
                "Murasalat Correspondence."
            )
        )

    open_referrals = _get_open_referrals(doc.name)

    if open_referrals:
        frappe.throw(
            _(
                "The correspondence cannot be closed while it has "
                "open referrals."
            )
        )

    doc.closed_on = now_datetime()

    _append_activity(
        doc,
        "Closed",
        _("Correspondence officially closed."),
    )


def seal_correspondence(doc):
    if doc.doctype != "Murasalat Correspondence":
        frappe.throw(
            _(
                "Seal Correspondence can only run on "
                "Murasalat Correspondence."
            )
        )

    if doc.record_sealed_on:
        return

    doc.record_sealed_on = now_datetime()
    doc.record_sealed_by = frappe.session.user

    _append_activity(
        doc,
        "Sealed",
        _("Correspondence integrity snapshot sealed."),
    )


def reopen_correspondence(doc):
    """Reopen a correspondence and lift any seal on it.

    There is no silent way to amend a sealed record. Amending one means
    reopening it: the previous snapshot is written to the activity trail, the
    seal is lifted, and the record must be sealed again afterwards, which
    produces a new snapshot. A reason is mandatory so the amendment is
    attributable.
    """
    if doc.doctype != "Murasalat Correspondence":
        frappe.throw(
            _(
                "Reopen Correspondence can only run on "
                "Murasalat Correspondence."
            )
        )

    was_sealed = bool(doc.get("record_sealed_on") or doc.get("integrity_hash"))

    # Idempotent: reopening an open, unsealed record changes nothing.
    if not doc.get("closed_on") and not was_sealed:
        return

    reason = (doc.get("reopen_reason") or "").strip()

    if not reason:
        frappe.throw(
            _(
                "A reason is required to reopen a correspondence, because "
                "reopening lifts the integrity seal."
            )
        )

    previous_snapshot = doc.get("integrity_hash")
    previous_sealed_on = doc.get("record_sealed_on")
    previous_sealed_by = doc.get("record_sealed_by")

    doc.reopened_on = now_datetime()
    doc.reopened_by = frappe.session.user

    # closed_on represents the current/latest closure state. Historical
    # reopen/close events remain in the Activity table and Frappe Version history.
    doc.closed_on = None

    _append_activity(
        doc,
        "Reopened",
        _("Correspondence was reopened. Reason: {0}").format(reason),
    )

    if was_sealed:
        # The old snapshot survives in the activity trail, so the record can
        # still be proven to have existed in that exact form.
        _append_activity(
            doc,
            "Unsealed",
            _(
                "Integrity seal lifted to allow a documented amendment. "
                "Previous snapshot: {0} (sealed on {1} by {2})."
            ).format(
                previous_snapshot or _("none"),
                previous_sealed_on or _("unknown"),
                previous_sealed_by or _("unknown"),
            ),
        )

        doc.record_sealed_on = None
        doc.record_sealed_by = None
        doc.integrity_hash = None


def _get_referral_correspondence(doc):
    if not doc.correspondence:
        frappe.throw(
            _("A referral must be linked to a Correspondence.")
        )

    correspondence = frappe.get_doc(
        "Murasalat Correspondence",
        doc.correspondence,
    )
    correspondence.check_permission("read")
    return correspondence


def _ensure_correspondence_open_for_send(doc):
    correspondence = _get_referral_correspondence(doc)
    if correspondence.closed_on:
        frappe.throw(
            _("A referral cannot be sent because the Correspondence is closed.")
        )
    return correspondence

def send_referral(doc):
    if doc.doctype != "Murasalat Referral":
        frappe.throw(
            _("Send Referral can only run on Murasalat Referral.")
        )

    if doc.sent_on:
        return

    _validate_referral_for_transition(doc)
    _ensure_correspondence_open_for_send(doc)

    doc.sent_on = now_datetime()

    _append_referral_activity(
        doc,
        "Referral Sent",
        _("Referral {0} was sent to {1}.").format(
            doc.referral_number or doc.name,
            (
                doc.recipient_user
                if doc.recipient_type == "User"
                else doc.recipient_department
            ),
        ),
    )


def receive_referral(doc):
    if doc.doctype != "Murasalat Referral":
        frappe.throw(
            _("Receive Referral can only run on Murasalat Referral.")
        )

    _validate_referral_for_transition(doc)

    if not doc.sent_on:
        frappe.throw(
            _("A referral must be sent before it can be received.")
        )

    if not doc.received_on:
        doc.received_on = now_datetime()
        doc.received_by = frappe.session.user

        _append_referral_activity(
            doc,
            "Referral Received",
            _("Referral {0} was received.").format(
                doc.referral_number or doc.name,
            ),
        )

    if not doc.correspondence:
        return

    # A Department-targeted referral moves the organizational holder.
    # A User-targeted referral does NOT create a second holder model:
    # the Referral + native ToDo identify the personal work assignment.
    if (
        doc.recipient_type != "Department"
        or not doc.recipient_department
    ):
        return

    correspondence = frappe.get_doc(
        "Murasalat Correspondence",
        doc.correspondence,
    )

    correspondence.check_permission("write")

    correspondence.current_holder = doc.recipient_department

    # Legacy/deprecated projection must never be used as a user assignment
    # source of truth.
    if hasattr(correspondence, "current_holder_user"):
        correspondence.current_holder_user = None

    correspondence.save()


def complete_referral(doc):
    if doc.doctype != "Murasalat Referral":
        frappe.throw(
            _("Complete Referral can only run on Murasalat Referral.")
        )

    _validate_referral_for_transition(doc)

    if not doc.sent_on:
        frappe.throw(
            _("A referral must be sent before it can be completed.")
        )

    if not doc.received_on:
        frappe.throw(
            _("A referral must be received before it can be completed.")
        )

    if doc.completed_on:
        return

    doc.completed_on = now_datetime()
    doc.completed_by = frappe.session.user

    _append_referral_activity(
        doc,
        "Referral Completed",
        _("Referral {0} was completed.").format(
            doc.referral_number or doc.name,
        ),
    )


def _validate_referral_for_transition(doc):
    """Delegate to the controller's own invariants so the two layers cannot drift.

    ``Murasalat Referral.validate()`` already runs these three rules on every save.
    Calling them here as well makes a failing transition report its reason before any
    lifecycle field is stamped, instead of failing later inside the transition's save.
    """
    doc._validate_recipient()
    doc._validate_dates()
    doc._validate_correspondence()