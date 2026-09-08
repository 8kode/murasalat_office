import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime


class MurasalatApprovalRequest(Document):
    def validate(self):
        if not self.correspondence:
            frappe.throw(_("Correspondence is required."))
        if not self.requested_by:
            self.requested_by = frappe.session.user
        if not self.requested_on:
            self.requested_on = now_datetime()
        if not self.approval_level or self.approval_level < 1:
            frappe.throw(_("Approval Level must be at least 1."))

    def after_insert(self):
        self._sync_correspondence("Approval Requested", "Approval request created.", "Under Review")

    def on_update(self):
        before = self.get_doc_before_save()
        old_state = getattr(before, "workflow_state", None) if before else None
        if old_state == self.workflow_state:
            return
        mapping = {
            "Under Review": ("Approval Review Started", "Approval request entered review.", "Under Review"),
            "Under Approval": ("Approval Submitted", "Approval request entered formal approval.", "Under Approval"),
            "Approved": ("Approval Granted", "Correspondence approved through the formal workflow.", "Approved"),
            "Rejected": ("Approval Rejected", "Approval request rejected through the formal workflow.", "Rejected"),
            "Draft": ("Approval Returned", "Approval request returned for amendment.", "Registered"),
        }
        if self.workflow_state in mapping:
            activity_type, details, status = mapping[self.workflow_state]
            if self.workflow_state == "Approved":
                self.db_set("approved_by", frappe.session.user, update_modified=False)
                self.db_set("approved_on", now_datetime(), update_modified=False)
            self._sync_correspondence(activity_type, details, status)

    def _sync_correspondence(self, activity_type, details, status=None):
        correspondence = frappe.get_doc("Murasalat Correspondence", self.correspondence)
        if status:
            correspondence.status = status
        correspondence.append("activities", {
            "activity_type": activity_type,
            "activity_on": now_datetime(),
            "actor": frappe.session.user,
            "details": details,
        })
        correspondence.flags.murasalat_approval_sync = True
        correspondence.save(ignore_permissions=True)
