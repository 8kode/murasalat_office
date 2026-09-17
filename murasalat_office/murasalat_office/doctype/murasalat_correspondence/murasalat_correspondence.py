import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime

from murasalat_office.services.records import (
    compute_integrity_hash,
    validate_immutable_fields,
    validate_sealed_attachments,
    verify_integrity,
)


class MurasalatCorrespondence(Document):
    """Correspondence document.

    Authorization and lifecycle transitions are delegated to native Frappe/ERPNext
    permissions and Workflow configuration maintained from Desk.
    """

    def validate(self):
        validate_immutable_fields(self)
        validate_sealed_attachments(self)
        self._validate_links()

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
                "Integrity verification failed. "
                "Sealed record content differs from its snapshot."
            )

    def _validate_links(self):
        seen = set()

        for row in self.links or []:
            if row.linked_correspondence == self.name:
                frappe.throw(
                    "A correspondence cannot link to itself."
                )

            key = (
                row.linked_correspondence,
                row.relationship_type,
            )

            if key in seen:
                frappe.throw(
                    "Duplicate correspondence link detected."
                )

            seen.add(key)

    def before_insert(self):
        self._append_activity(
            "Created",
            details="Correspondence created.",
        )

    def before_save(self):
        """Record generic Workflow state changes.

        Registration, closure, sealing and reopening are owned by explicit
        Workflow Transition Tasks and are intentionally not duplicated here.
        """
        if self.is_new():
            return

        old = self.get_doc_before_save()

        if not old:
            return

        if old.workflow_state != self.workflow_state:
            self._append_activity(
                "Status Changed",
                details=(
                    f"Workflow state changed from "
                    f"{old.workflow_state or 'unset'} to "
                    f"{self.workflow_state or 'unset'}."
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
                        "recipient_organization",
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