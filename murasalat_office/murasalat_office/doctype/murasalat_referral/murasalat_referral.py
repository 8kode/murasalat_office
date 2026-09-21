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
            if not self.recipient_user or self.recipient_department:
                frappe.throw("User referrals require a user recipient and no organization recipient.")
        elif self.recipient_type == "Department":
            if not self.recipient_department or self.recipient_user:
                frappe.throw("Department referrals require an Department recipient and no user recipient.")
        else:
            frappe.throw("Recipient Type must be User or Department.")
