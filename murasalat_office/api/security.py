import frappe
from frappe import _
from murasalat_office.security.permissions import can_access_attachment


def _doc_and_row(correspondence, attachment_name):
    doc = frappe.get_doc("Murasalat Correspondence", correspondence)
    doc.check_permission("read")
    for row in doc.attachments or []:
        if row.name == attachment_name:
            return doc, row
    frappe.throw(_("Attachment not found."), frappe.DoesNotExistError)


@frappe.whitelist()
def attachment_access(correspondence, attachment_name, action="view"):
    if action not in {"view", "download"}:
        frappe.throw(_("Invalid attachment action."))
    doc, row = _doc_and_row(correspondence, attachment_name)
    if not can_access_attachment(doc, row, action=action):
        frappe.throw(_("You are not permitted to access this attachment."), frappe.PermissionError)
    return {"file_url": row.file, "is_secret": int(row.is_secret or 0), "action": action}
