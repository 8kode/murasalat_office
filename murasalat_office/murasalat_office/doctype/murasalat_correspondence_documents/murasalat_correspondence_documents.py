from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document


class MurasalatCorrespondenceDocuments(Document):
    def validate(self):
        if self.is_main_document and frappe.db.exists(
            "Murasalat Correspondence Document",
            {
                "correspondence": self.correspondence,
                "is_main_document": 1,
                "name": ["!=", self.name or ""],
            },
        ):
            frappe.throw(
                _("Only one main document is allowed for a correspondence.")
            )