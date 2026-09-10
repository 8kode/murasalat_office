import frappe
from frappe.model.document import Document


class MurasalatReferral(Document):
    """Standalone referral; permissions and lifecycle are native Desk configuration."""

    def before_insert(self):
        # Frappe's naming engine has already generated the document name by this point.
        # Keep a human-readable, stable display number without creating a second counter.
        if not self.referral_number:
            self.referral_number = self.name

    def validate(self):
        if self.recipient_type == "User":
            if not self.recipient_user or self.recipient_organization:
                frappe.throw("User referrals require a user recipient and no organization recipient.")
        elif self.recipient_type == "Organization":
            if not self.recipient_organization or self.recipient_user:
                frappe.throw("Organization referrals require an organization recipient and no user recipient.")
        else:
            frappe.throw("Recipient Type must be User or Organization.")
