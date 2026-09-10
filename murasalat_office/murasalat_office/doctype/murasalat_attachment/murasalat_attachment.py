import frappe
from frappe import _
from frappe.model.document import Document

from murasalat_office.services.records import hash_file_url


class MurasalatAttachment(Document):
    def validate(self):
        if not self.file:
            return

        old = self.get_doc_before_save()
        file_changed = not old or old.file != self.file
        if file_changed or not self.file_hash:
            file_hash = hash_file_url(self.file)
            if not file_hash:
                frappe.throw(_("Unable to calculate the attachment integrity hash. Please verify that the uploaded File is available."))
            self.file_hash = file_hash
