import hashlib
import json

import frappe
from frappe import _


# Fields that become immutable once the correspondence is sealed. Registration
# and sealing are distinct lifecycle events; immutability starts at sealing.
IMMUTABLE_AFTER_SEALING = {
    "correspondence_type",
    "transaction_type",
    "confidentiality",
    "importance",
    "external_letter_number",
    "external_letter_date",
    "source_entity",
    "target_entity",
    "originating_organization",
    "subject",
    "page_count",
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
            {
                "file": row.file,
                "hash": row.file_hash,
                "secret": row.is_secret,
                "type": row.attachment_type,
                "folder": row.folder,
            }
            for row in (doc.attachments or [])
        ],
    }
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def compute_integrity_hash(doc):
    return hashlib.sha256(canonical_payload(doc).encode()).hexdigest()


def _attachment_snapshot(doc):
    return [
        (
            row.file,
            row.file_hash,
            row.is_secret,
            row.attachment_type,
            row.folder,
        )
        for row in (doc.attachments or [])
    ]


def validate_sealed_attachments(doc):
    """Prevent attachment-set changes after a correspondence is sealed."""
    if doc.is_new() or not doc.record_sealed_on:
        return

    old = doc.get_doc_before_save()
    if old and _attachment_snapshot(old) != _attachment_snapshot(doc):
        frappe.throw(_("Attachments cannot be added, removed, or changed after the correspondence is sealed."))


def validate_immutable_fields(doc):
    if doc.is_new() or not doc.record_sealed_on:
        return

    old = doc.get_doc_before_save()
    if not old:
        return

    changed = [field for field in IMMUTABLE_AFTER_SEALING if old.get(field) != doc.get(field)]
    if changed:
        frappe.throw(
            _(
                "Sealed correspondence identity/classification fields cannot be changed: {0}"
            ).format(", ".join(sorted(changed)))
        )


def hash_file_url(file_url: str | None) -> str | None:
    """Return the SHA-256 of a Frappe File's content by file URL."""
    if not file_url:
        return None

    name = frappe.db.get_value("File", {"file_url": file_url}, "name")
    if not name:
        return None

    content = frappe.get_doc("File", name).get_content()
    if isinstance(content, str):
        content = content.encode()
    return hashlib.sha256(content).hexdigest()


def verify_integrity(doc, verify_files: bool = True) -> bool:
    """Verify the stored integrity snapshot.

    ``verify_files=True`` performs the expensive content-hash check for each
    attachment and is intended for explicit integrity verification. Normal
    document saves can use ``verify_files=False`` because sealed attachment
    metadata and immutable fields are already validated before persistence.
    """
    if not doc.integrity_hash:
        return True

    if verify_files:
        for row in doc.attachments or []:
            if not row.file:
                continue
            # A sealed attachment without a stored hash cannot be verified.
            # Fail closed rather than treating missing evidence as valid.
            if not row.file_hash:
                return False
            current_hash = hash_file_url(row.file)
            if not current_hash or current_hash != row.file_hash:
                return False

    return compute_integrity_hash(doc) == doc.integrity_hash
