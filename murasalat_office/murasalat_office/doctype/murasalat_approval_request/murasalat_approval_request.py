import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime


def _val(doc, field, default=None):
    """Read a field without assuming the whole Document is materialised.

    Controllers are exercised against partially built objects, so a field that was
    never set must read as its default instead of raising.
    """
    if hasattr(doc, field):
        return getattr(doc, field)

    getter = getattr(doc, "get", None)

    if callable(getter):
        return getter(field, default)

    return default

class MurasalatApprovalRequest(Document):
    """Approval request data model; workflow authority belongs entirely to Desk."""

    def validate(self):
        if self.is_new():
            self.requested_by = frappe.session.user
            if not self.requested_on:
                self.requested_on = now_datetime()
            if _val(self, "approved_by") or _val(self, "approved_on"):
                frappe.throw(
                    _("An approval request cannot be created already approved."),
                    frappe.PermissionError,
                )

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

        self._freeze_decision(before)

    def _freeze_decision(self, before):
        """Stamp the decision once, by the acting user, and never rewrite it.

        ``approved_by``/``approved_on`` are ``read_only`` in the DocType, but Frappe
        does not enforce ``read_only`` server-side, so the field metadata alone leaves
        the decision forgeable through the API. These rules make the recorded approver
        unforgeable and the timestamp unbackdatable.
        """
        approved_by = _val(self, "approved_by")
        approved_on = _val(self, "approved_on")

        if not approved_by:
            if approved_on:
                frappe.throw(
                    _("Approved On cannot be recorded without Approved By."),
                    frappe.PermissionError,
                )
            return

        recorded_by = _val(before, "approved_by") if before else None
        recorded_on = _val(before, "approved_on") if before else None

        if recorded_by:
            if recorded_by != approved_by or recorded_on != approved_on:
                frappe.throw(
                    _("The approval decision is already recorded and cannot be changed."),
                    frappe.PermissionError,
                )
            return

        if approved_by != frappe.session.user:
            frappe.throw(
                _("Approved By must be the user recording the decision."),
                frappe.PermissionError,
            )

        if not approved_on:
            self.approved_on = now_datetime()
