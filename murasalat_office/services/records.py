import hashlib
import json

import frappe
from frappe import _
from frappe.utils import now_datetime

IMMUTABLE_AFTER_REGISTRATION = {
    "correspondence_type", "transaction_type", "confidentiality", "importance",
    "external_letter_number", "external_letter_date", "source_entity", "target_entity",
    "originating_organization", "subject", "page_count",
}


def canonical_payload(doc):
    data = {
        "name": doc.name,
        "correspondence_type": doc.correspondence_type,
        "transaction_type": doc.transaction_type,
        "confidentiality": doc.confidentiality,
        "importance": doc.importance,
        "subject": doc.subject,
        "external_letter_number": doc.external_letter_number,
        "external_letter_date": str(doc.external_letter_date or ""),
        "source_entity": doc.source_entity,
        "target_entity": doc.target_entity,
        "originating_organization": doc.originating_organization,
        "page_count": doc.page_count,
        "attachments": [
            {"file": r.file, "hash": r.file_hash, "secret": r.is_secret,
             "type": r.attachment_type, "folder": r.folder}
            for r in (doc.attachments or [])
        ],
    }
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def compute_integrity_hash(doc):
    return hashlib.sha256(canonical_payload(doc).encode()).hexdigest()


def seal(doc, reason="Registered"):
    doc.integrity_hash = compute_integrity_hash(doc)
    if not doc.record_sealed_on:
        doc.record_sealed_on = now_datetime()
    if not doc.record_sealed_by:
        doc.record_sealed_by = frappe.session.user
    doc.seal_reason = reason


def validate_immutable_fields(doc):
    if doc.is_new() or doc.status in {"Draft", "Reopened"}:
        return
    old = doc.get_doc_before_save()
    if not old:
        return
    changed = [f for f in IMMUTABLE_AFTER_REGISTRATION if old.get(f) != doc.get(f)]
    if changed:
        frappe.throw(_("Registered correspondence identity/classification fields cannot be changed: {0}").format(", ".join(sorted(changed))))


def verify_integrity(doc):
    if not doc.integrity_hash:
        return True
    return compute_integrity_hash(doc) == doc.integrity_hash
