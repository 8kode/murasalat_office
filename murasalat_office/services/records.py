import hashlib
import json

import frappe
from frappe import _


# Fields that become immutable once the correspondence is sealed.
IMMUTABLE_AFTER_SEALING = {
    "correspondence_direction",
    "transaction_type",
    "confidentiality",
    "importance",
    "external_letter_number",
    "external_letter_date",
    "incoming_source_entity",
    "incoming_target_entry",
    "outgoing_source_entity",
    "outgoing_target_entry",
    "internal_source_entity",
    "internal_target_entry",
    "originating_organization",
    "subject",
    "page_count",
    "seal_reason",
    "notes",
    "due_date",
    "concerned_person",
}


def canonical_payload(doc):
    data = {
        "name": doc.name,
        "correspondence_direction": doc.correspondence_direction,
        "transaction_type": doc.transaction_type,
        "confidentiality": doc.confidentiality,
        "importance": doc.importance,
        "subject": doc.subject,
        "external_letter_number": doc.external_letter_number,
        "external_letter_date": str(
            doc.external_letter_date or ""
        ),
        "incoming_source_entity": doc.incoming_source_entity,
        "incoming_target_entry": doc.incoming_target_entry,
        "outgoing_source_entity": doc.outgoing_source_entity,
        "outgoing_target_entry": doc.outgoing_target_entry,
        "internal_source_entity": doc.internal_source_entity,
        "internal_target_entry": doc.internal_target_entry,
        "originating_organization": doc.originating_organization,
        "seal_reason": doc.seal_reason,
        "page_count": doc.page_count,
        "notes": doc.notes,
        "due_date": str(doc.due_date or ""),
        "concerned_person": doc.concerned_person,
        "attachments": [
            {
                "file": row.file,
                "hash": row.file_hash,
                "secret": row.is_secret,
                "type": row.attachment_type,
                "archive_location": getattr(row, "archive_location", None),
            }
            for row in (doc.attachments or [])
        ],
        "linked_files": _linked_file_snapshot(doc),
    }

    return json.dumps(
        data,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _linked_file_snapshot(doc):
    """Files attached to the record outside the attachment table.

    An upload lands as a ``File`` linked by ``attached_to_doctype``/``attached_to_name``,
    and a gallery field stores its files the same way. Those files are not rows in
    ``attachments``, so a snapshot built only from that table left them outside the seal:
    a file could be added to or replaced on a sealed record and every integrity check
    would still pass. Read them directly, so the seal covers whatever the record can
    actually show.
    """
    name = getattr(doc, "name", None)
    doctype = getattr(doc, "doctype", None)

    if not name or not doctype:
        return []

    rows = frappe.get_all(
        "File",
        filters={"attached_to_doctype": doctype, "attached_to_name": name},
        fields=["name", "file_url", "file_name"],
        order_by="name asc",
        limit_page_length=0,
    )

    return [[row.name, row.file_url, row.file_name] for row in rows]


def compute_integrity_hash(doc):
    return hashlib.sha256(
        canonical_payload(doc).encode()
    ).hexdigest()


def _attachment_snapshot(doc):
    """Everything that identifies the record's attachment set.

    Covers both the attachment table and the files linked to the record natively, so
    adding a file through the gallery or the standard uploader is caught just like adding
    a row.
    """
    return (
        [
            (
                row.file,
                row.file_hash,
                row.is_secret,
                row.attachment_type,
                getattr(row, "archive_location", None),
            )
            for row in (doc.attachments or [])
        ],
        _linked_file_snapshot(doc),
    )


def validate_sealed_attachments(doc):
    """Prevent attachment-set changes after a correspondence is sealed."""
    if doc.is_new() or not doc.record_sealed_on:
        return

    old = doc.get_doc_before_save()

    if old and _attachment_snapshot(old) != _attachment_snapshot(doc):
        frappe.throw(
            _(
                "Attachments cannot be added, removed, or changed "
                "after the correspondence is sealed."
            )
        )


def validate_immutable_fields(doc):
    if doc.is_new() or not doc.record_sealed_on:
        return

    old = doc.get_doc_before_save()

    if not old:
        return

    changed = [
        field
        for field in IMMUTABLE_AFTER_SEALING
        if old.get(field) != doc.get(field)
    ]

    if changed:
        frappe.throw(
            _(
                "Sealed correspondence identity/classification fields "
                "cannot be changed: {0}"
            ).format(
                ", ".join(sorted(changed))
            )
        )


def hash_file_url(file_url: str | None) -> str | None:
    """Return SHA-256 of a Frappe File's content."""
    if not file_url:
        return None

    # Two File rows can share a file_url (a private and a public copy, for instance), and
    # the newest is the one the record is actually showing. An explicit ordered lookup
    # keeps the hash tied to that copy instead of to whichever row came back first.
    rows = frappe.get_all(
        "File",
        filters={"file_url": file_url},
        fields=["name"],
        order_by="creation desc",
        limit_page_length=1,
    )

    if not rows:
        return None

    content = frappe.get_doc(
        "File",
        rows[0].name,
    ).get_content()

    if isinstance(content, str):
        content = content.encode()

    return hashlib.sha256(content).hexdigest()


def verify_integrity(
    doc,
    verify_files: bool = True,
) -> bool:
    """Verify the stored integrity snapshot."""

    # A record that declares itself sealed but carries no snapshot cannot be
    # verified; returning True there would report a broken seal as intact.
    if not doc.integrity_hash:
        return not doc.record_sealed_on

    if verify_files:
        for row in doc.attachments or []:
            if not row.file:
                continue

            if not row.file_hash:
                return False

            current_hash = hash_file_url(row.file)

            if (
                not current_hash
                or current_hash != row.file_hash
            ):
                return False

    return (
        compute_integrity_hash(doc)
        == doc.integrity_hash
    )