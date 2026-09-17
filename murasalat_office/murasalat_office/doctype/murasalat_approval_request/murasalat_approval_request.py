import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime


class MurasalatApprovalRequest(Document):
    """Approval request data model; workflow authority belongs entirely to Desk."""

    def validate(self):
        if self.is_new():
            self.requested_by = frappe.session.user
            if not self.requested_on:
                self.requested_on = now_datetime()

        before = self.get_doc_before_save()
        if before and before.requested_by != self.requested_by:
            frappe.throw(_("Requested By cannot be changed after creation."), frappe.PermissionError)
        if before and before.correspondence != self.correspondence:
            frappe.throw(_("Correspondence cannot be changed after creation."), frappe.PermissionError)
        if not self.correspondence:
            frappe.throw(_("Correspondence is required."))
        if not self.requested_by:
            self.requested_by = frappe.session.user
        if not self.approval_level or self.approval_level < 1:
            frappe.throw(_("Approval Level must be at least 1."))
