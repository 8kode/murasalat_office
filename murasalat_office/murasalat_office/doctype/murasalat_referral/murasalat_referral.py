import frappe
from frappe import _
from frappe.model.document import Document

from murasalat_office.services.records import validate_attachment_rows


class MurasalatReferral(Document):
    """Standalone referral; permissions and lifecycle are native Desk configuration.

    Unconditional domain invariants live here, in ``validate()``, so they hold on
    every save — including a direct form edit or an API insert that never passes
    through a Workflow transition. The transition methods in ``services.lifecycle``
    call these same rules instead of restating them, so the two layers cannot drift.
    """

    def before_insert(self):
        # Frappe's naming engine has already generated the document name by this point.
        # Keep a human-readable, stable display number without creating a second counter.
        if not self.referral_number:
            self.referral_number = self.name

    def validate(self):
        self._validate_recipient()
        self._validate_dates()
        self._validate_correspondence()
        validate_attachment_rows(self)

    def _validate_recipient(self):
        """Exactly one recipient, and it must match the recipient type."""
        if self.recipient_type == "User":
            if not self.recipient_user or self.recipient_department:
                frappe.throw(
                    _(
                        "User referrals require a user recipient "
                        "and no department recipient."
                    )
                )
        elif self.recipient_type == "Department":
            if not self.recipient_department or self.recipient_user:
                frappe.throw(
                    _(
                        "Department referrals require a department recipient "
                        "and no user recipient."
                    )
                )
        else:
            frappe.throw(
                _("Recipient Type must be User or Department.")
            )

    def _validate_dates(self):
        """Receipt requires sending; completion requires receipt.

        A due date in the past stays valid: an already overdue referral is a
        legitimate operational state, and the report layer decides whether it is
        still open.
        """
        if self.completed_on and not self.received_on:
            frappe.throw(
                _("A referral cannot be completed before it is received.")
            )

        if self.received_on and not self.sent_on:
            frappe.throw(
                _("A referral cannot be received before it is sent.")
            )

    def _validate_correspondence(self):
        """A new referral may not be opened on a closed correspondence.

        Scoped to creation on purpose: editing an existing referral has to stay
        possible after the file it belongs to is closed. The check reads the parent
        through the normal ORM and applies native Frappe read permission rather than
        a bespoke access rule.
        """
        if not self.correspondence:
            frappe.throw(
                _("A referral must be linked to a Correspondence.")
            )

        if not self.is_new():
            return

        correspondence = frappe.get_doc(
            "Murasalat Correspondence",
            self.correspondence,
        )
        correspondence.check_permission("read")

        if correspondence.closed_on:
            frappe.throw(
                _(
                    "A new referral cannot be created because the "
                    "Correspondence is closed."
                )
            )
