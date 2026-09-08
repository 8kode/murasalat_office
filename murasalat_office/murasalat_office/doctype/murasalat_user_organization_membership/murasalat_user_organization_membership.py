import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate


class MurasalatUserOrganizationMembership(Document):
    def validate(self):
        if self.valid_from and self.valid_to and getdate(self.valid_from) > getdate(self.valid_to):
            frappe.throw(_("Valid From cannot be after Valid To."))
        duplicate = frappe.db.exists(
            self.doctype,
            {"user": self.user, "organization": self.organization, "name": ["!=", self.name]},
        )
        if duplicate:
            frappe.throw(_("A membership for this user and organization already exists."))
