import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime

from murasalat_office.services.records import (
    compute_integrity_hash,
    validate_immutable_fields,
    validate_sealed_attachments,
    verify_integrity,
)


DIRECTION_FIELDS = {
    "Incoming": (
        "incoming_source_entity",
        "incoming_target_entry",
    ),
    "Outgoing": (
        "outgoing_source_entity",
        "outgoing_target_entry",
    ),
    "Internal": (
        "internal_source_entity",
        "internal_target_entry",
    ),
}

ALL_DIRECTION_FIELDS = tuple(
    field
    for fields in DIRECTION_FIELDS.values()
    for field in fields
)


class MurasalatCorrespondence(Document):
    """Administrative correspondence record.

    Native Frappe/ERPNext permissions and Workflow remain the authorization
    boundary. This controller enforces domain/data invariants only.
    """

    def validate(self):
        self._validate_direction()
        self._validate_direction_exclusivity()
        self._validate_numeric_fields()
        self._validate_links()

        validate_immutable_fields(self)
        validate_sealed_attachments(self)

        if self.record_sealed_on and not self.integrity_hash:
            self.integrity_hash = compute_integrity_hash(self)

        if (
            self.integrity_hash
            and not self.is_new()
            and not verify_integrity(
                self,
                verify_files=False,
            )
        ):
            frappe.throw(
                _(
                    "Integrity verification failed. "
                    "Sealed record content differs from its snapshot."
                )
            )

    def _validate_direction(self):
        """Require the correct source/target parties for the direction.

        Client-side mandatory_depends_on is useful UX, but it is not a
        sufficient server-side invariant. This method is the authoritative
        data validation.
        """
        direction = self.correspondence_direction

        if direction not in DIRECTION_FIELDS:
            frappe.throw(
                _(
                    "Correspondence Direction must be Incoming, Outgoing, "
                    "or Internal."
                )
            )

        required_fields = DIRECTION_FIELDS[direction]

        missing = [
            field
            for field in required_fields
            if not self.get(field)
        ]

        if missing:
            labels = {
                "incoming_source_entity": _("Sender"),
                "incoming_target_entry": _("Receiving Department"),
                "outgoing_source_entity": _("Sending Department"),
                "outgoing_target_entry": _("External Recipient"),
                "internal_source_entity": _("Source Department"),
                "internal_target_entry": _("Target Department"),
            }

            frappe.throw(
                _(
                    "The following fields are required for {0}: {1}"
                ).format(
                    _(direction),
                    ", ".join(
                        labels.get(field, field)
                        for field in missing
                    ),
                )
            )

    def _validate_direction_exclusivity(self):
        """Reject stale values belonging to a different direction."""
        direction = self.correspondence_direction
        allowed = set(DIRECTION_FIELDS[direction])
        stale = [
            field
            for field in ALL_DIRECTION_FIELDS
            if field not in allowed and self.get(field)
        ]

        if stale:
            labels = {
                "incoming_source_entity": _("Incoming Sender"),
                "incoming_target_entry": _("Incoming Receiving Department"),
                "outgoing_source_entity": _("Outgoing Sending Department"),
                "outgoing_target_entry": _("Outgoing External Recipient"),
                "internal_source_entity": _("Internal Source Department"),
                "internal_target_entry": _("Internal Target Department"),
            }
            frappe.throw(
                _("Fields from another correspondence direction contain values: {0}. Clear them before saving.").format(
                    ", ".join(labels.get(field, field) for field in stale)
                )
            )

    def _validate_numeric_fields(self):
        if self.page_count is not None and self.page_count < 0:
            frappe.throw(_("Page Count cannot be negative."))

    def _validate_links(self):
        seen = set()

        for row in self.links or []:
            if not row.linked_correspondence:
                continue

            if row.linked_correspondence == self.name:
                frappe.throw(
                    _("A correspondence cannot link to itself.")
                )

            key = (
                row.linked_correspondence,
                row.relationship_type,
            )

            if key in seen:
                frappe.throw(
                    _("Duplicate correspondence link detected.")
                )

            seen.add(key)

    def before_insert(self):
        self._append_activity(
            "Created",
            details=_("Correspondence created."),
        )

    def before_save(self):
        """Record Workflow state changes.

        Business transitions themselves remain Workflow-owned. This hook only
        records the resulting state change in the domain activity table.
        """
        if self.is_new():
            return

        old = self.get_doc_before_save()

        if not old:
            return

        if old.workflow_state != self.workflow_state:
            self._append_activity(
                "Status Changed",
                details=_(
                    "Workflow state changed from {0} to {1}."
                ).format(
                    old.workflow_state or _("unset"),
                    self.workflow_state or _("unset"),
                ),
            )

    def _append_activity(
        self,
        activity_type,
        referral=None,
        details=None,
    ):
        self.append(
            "activities",
            {
                "activity_type": activity_type,
                "activity_on": now_datetime(),
                "actor": frappe.session.user,
                "organization": (
                    getattr(
                        referral,
                        "recipient_department",
                        None,
                    )
                    if referral
                    else self.current_holder
                ),
                "referral_number": (
                    getattr(
                        referral,
                        "referral_number",
                        None,
                    )
                    if referral
                    else None
                ),
                "details": details,
            },
        )