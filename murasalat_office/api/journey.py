import frappe
from murasalat_office.services import journey


def _get(name):
    doc = frappe.get_doc("Murasalat Correspondence", name)
    doc.check_permission("write")
    return doc


@frappe.whitelist()
def registration_checklist(correspondence):
    doc = _get(correspondence)
    return {"ready": not journey.validate_registration_ready(doc), "errors": journey.validate_registration_ready(doc)}


@frappe.whitelist()
def register(correspondence):
    doc = _get(correspondence)
    doc = journey.register(doc)
    return {"name": doc.name, "status": doc.status, "registered_on": doc.registered_on}


@frappe.whitelist()
def send(correspondence):
    doc = _get(correspondence)
    doc = journey.send(doc)
    return {"name": doc.name, "status": doc.status}
