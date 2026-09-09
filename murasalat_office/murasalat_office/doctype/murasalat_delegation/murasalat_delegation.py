import frappe
from frappe.model.document import Document
from frappe.utils import getdate


class MurasalatDelegation(Document):
    def validate(self):
        if self.delegator == self.delegate:
            frappe.throw("Delegator and delegate cannot be the same user.")
        if getdate(self.from_date) > getdate(self.to_date):
            frappe.throw("Delegation end date must be on or after start date.")
        # Access is governed exclusively by native DocPerm/User Permissions.
