import hashlib
import frappe
from frappe.model.document import Document

class MurasalatAttachment(Document):
    def validate(self):
        if self.file and not self.file_hash:
            self.file_hash = self._hash_file_url(self.file)

    @staticmethod
    def _hash_file_url(file_url):
        name = frappe.db.get_value("File", {"file_url": file_url}, "name")
        if not name:
            return None
        file_doc = frappe.get_doc("File", name)
        try:
            content = file_doc.get_content()
        except Exception:
            return None
        if isinstance(content, str):
            content = content.encode()
        return hashlib.sha256(content).hexdigest()
