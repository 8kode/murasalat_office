import frappe
from frappe.model.document import Document


class MurasalatReferral(Document):
    """Standalone referral. Authorization and lifecycle transitions are native Frappe Workflow/permissions."""

    def validate(self):
        if self.recipient_type == "User":
            if not self.recipient_user or self.recipient_organization:
                frappe.throw("A User referral must have a recipient user and no recipient organization.")
        elif self.recipient_type == "Organization":
            if not self.recipient_organization or self.recipient_user:
                frappe.throw("An Organization referral must have a recipient organization and no recipient user.")
        else:
            frappe.throw("Invalid referral recipient type.")
