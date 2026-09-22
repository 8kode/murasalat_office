import frappe
from frappe import _
from frappe.model.document import Document


class MurasalatReferral(Document):
    """Routing/work unit for a Murasalat Correspondence.

    Authorization is native Frappe/ERPNext. This controller only enforces
    domain invariants that cannot safely be left to client-side UI rules.
    """

    def before_insert(self):
        # Frappe's naming engine has already generated the document name.
        # Use that stable name as the human-readable referral number.
        if not self.referral_number:
            self.referral_number = self.name

    def validate(self):
        self._validate_recipient()
        self._validate_dates()
        self._validate_correspondence()

    def _validate_recipient(self):
        if self.recipient_type == "User":
            if not self.recipient_user:
                frappe.throw(
                    _("User referrals require a user recipient.")
                )

            if self.recipient_department:
                frappe.throw(
                    _(
                        "A User referral cannot also have a Department recipient."
                    )
                )

        elif self.recipient_type == "Department":
            if not self.recipient_department:
                frappe.throw(
                    _("Department referrals require a department recipient.")
                )

            if self.recipient_user:
                frappe.throw(
                    _(
                        "A Department referral cannot also have a User recipient."
                    )
                )

        else:
            frappe.throw(
                _("Recipient Type must be User or Department.")
            )

    def _validate_dates(self):
        # A past due date is allowed because an already-overdue referral
        # is a legitimate operational state. The report layer decides whether
        # it is currently open/overdue.
        #
        # What is not allowed is completion before receipt.
        if self.completed_on and not self.received_on:
            frappe.throw(
                _("A referral cannot be completed before it is received.")
            )

        if self.received_on and not self.sent_on:
            frappe.throw(
                _("A referral cannot be received before it is sent.")
            )

    def _validate_correspondence(self):
        if not self.correspondence:
            frappe.throw(
                _("A referral must be linked to a Correspondence.")
            )

        correspondence = frappe.get_doc(
            "Murasalat Correspondence",
            self.correspondence,
        )
        correspondence.check_permission("read")

        if self.is_new() and correspondence.closed_on:
            frappe.throw(
                _("A new referral cannot be created because the Correspondence is closed.")
            )