import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime

from murasalat_office.services.records import (
    compute_integrity_hash,
    validate_immutable_fields,
    validate_sealed_attachments,
    verify_integrity,
)

CORRESPONDENCE_PARTY_RULES = {
    "Internal": {
        "source": "Internal",
        "target": "Internal",
    },
    "Incoming": {
        "source": "External",
        "target": "Internal",
    },
    "Outgoing": {
        "source": "Internal",
        "target": "External",
    },
}


class MurasalatCorrespondence(Document):
    """Correspondence document.

    Authorization and lifecycle transitions are delegated to native Frappe/ERPNext
    permissions and Workflow configuration maintained from Desk.
    """

    def validate(self):
        validate_immutable_fields(self)
        validate_sealed_attachments(self)
        self._sync_originating_organization()
        self._validate_links()
        if self.record_sealed_on and not self.integrity_hash:
            self.integrity_hash = compute_integrity_hash(self)
        if (
            self.integrity_hash
            and not self.is_new()
            and not verify_integrity(self, verify_files=False)
        ):
            frappe.throw(
                "Integrity verification failed. Sealed record content differs from its snapshot."
            )
            
            
    def _validate_party_entities(self):
        rule = CORRESPONDENCE_PARTY_RULES.get(self.correspondence_type)

        if not rule:
            frappe.throw(
                frappe._("Invalid Correspondence Type: {0}").format(
                    self.correspondence_type
                )
            )

        if not self.source_entity:
            frappe.throw(frappe._("Source Entity is required."))

        if not self.target_entity:
            frappe.throw(frappe._("Target Entity is required."))

        source_type = frappe.db.get_value(
            "Murasalat Organization Entity",
            self.source_entity,
            "entity_type",
        )

        target_type = frappe.db.get_value(
            "Murasalat Organization Entity",
            self.target_entity,
            "entity_type",
        )

        if source_type != rule["source"]:
            frappe.throw(
                frappe._(
                    "Source Entity must be {0} for {1} correspondence."
                ).format(rule["source"], self.correspondence_type)
            )

        if target_type != rule["target"]:
            frappe.throw(
                frappe._(
                    "Target Entity must be {0} for {1} correspondence."
                ).format(rule["target"], self.correspondence_type)
            )

    def _validate_links(self):
        seen = set()
        for row in self.links or []:
            if row.linked_correspondence == self.name:
                frappe.throw("A correspondence cannot link to itself.")
            key = (row.linked_correspondence, row.relationship_type)
            if key in seen:
                frappe.throw("Duplicate correspondence link detected.")
            seen.add(key)

    def _sync_originating_organization(self):
        # Semantics: originating_organization identifies the organization/entity
        # recorded in source_entity; target_entity is only a fallback when source
        # is unavailable. This is descriptive metadata, not an authorization rule.
        # Keep it aligned while the record is mutable; once sealed, the snapshot
        # is preserved by the native document lifecycle and validation rules.
        if self.record_sealed_on:
            return
        derived = self.source_entity or self.target_entity
        if derived and self.originating_organization != derived:
            self.originating_organization = derived

    def before_insert(self):
        self._append_activity("Created", details="Correspondence created.")

    def before_save(self):
        """Record lifecycle events that are observable on the correspondence itself.

        Referral and approval transitions remain native child/standalone document
        history; this child table intentionally records only events this controller
        can observe without bypassing permissions or inventing workflow states.
        """
        if self.is_new():
            return

        old = self.get_doc_before_save()
        if not old:
            return

        if old.workflow_state != self.workflow_state:
            self._append_activity(
                "Status Changed",
                details=f"Workflow state changed from {old.workflow_state or 'unset'} to {self.workflow_state or 'unset'}.",
            )

        if not old.record_sealed_on and self.record_sealed_on:
            self._append_activity(
                "Sealed", details="Correspondence integrity snapshot sealed."
            )

        if not old.reopened_on and self.reopened_on:
            self._append_activity("Reopened", details="Correspondence was reopened.")

    def _append_activity(self, activity_type, referral=None, details=None):
        self.append(
            "activities",
            {
                "activity_type": activity_type,
                "activity_on": now_datetime(),
                "actor": frappe.session.user,
                "organization": (
                    getattr(referral, "recipient_organization", None)
                    if referral
                    else self.current_holder
                ),
                "referral_number": (
                    getattr(referral, "referral_number", None) if referral else None
                ),
                "details": details,
            },
        )