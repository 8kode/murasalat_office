"""File every record-level attachment in the record's attachments table.

Frappe has exactly one way to attach a file to a document: a ``File`` row carrying
``attached_to_doctype`` and ``attached_to_name``. The sidebar panel, drag-and-drop, the REST
upload endpoint and a row's own Attach control all go through it. The attachments table is a
second thing, and it can only describe what a file *is* - its type, where the paper original
is filed, whether it is secret.

Previous approach hid Frappe's panel with a DOM selector so the table would be the only
visible list. That worked against the framework and reached into markup it does not publish.
This module does the opposite: it listens on the framework's own extension point and lets the
panel feed the table. Whichever door a file comes through, it lands in the table, and the
panel is left exactly as Frappe built it.

``attached_to_field`` is what separates the two cases. ``frappe/client.py::attach_file`` sets
it from the ``docfield`` argument, so it is empty for an upload aimed at the record and holds
the field name when the user uploaded into a specific field. A field upload is the user
filling that row themselves - indexing it too would file the same file twice.

A sealed record refuses the file in ``File.before_insert``, before the framework stores it.
That is a real refusal rather than a hidden button: the rule holds for the REST endpoint and
drag-and-drop as well, not only for a user clicking in the Desk.
"""
import frappe
from frappe import _

# The DocTypes that own an attachments table fed by this module.
INDEXED_DOCTYPES = ("Murasalat Correspondence", "Murasalat Referral")

# Only a correspondence is sealed; a referral carries no seal fields. Mapping the DocType to
# its own field keeps the guard honest on the second DocType instead of probing for a column
# that is not there.
SEALED_DOCTYPES = {"Murasalat Correspondence": "record_sealed_on"}

TABLE_DOCTYPE = "Murasalat Attachment"
TABLE_FIELD = "attachments"
DEFAULT_TYPE = "Attachment"


def should_index(attached_to_doctype, attached_to_field=None):
    """True when a File row belongs in a record's attachments table.

    Pure so the decision can be tested without a site: a file aimed at one of our records at
    record level is ours to file; a file aimed at a field belongs to that field's row.
    """
    if attached_to_doctype not in INDEXED_DOCTYPES:
        return False

    return not attached_to_field


def refuse_file_on_a_sealed_record(doc, method=None):
    """``File.before_insert`` - a sealed record takes no new attachments.

    Raising here stops the insert, so the file is never stored and no orphan is left behind.
    """
    seal_field = SEALED_DOCTYPES.get(doc.attached_to_doctype)

    if not seal_field or not doc.attached_to_name:
        return

    if frappe.db.get_value(doc.attached_to_doctype, doc.attached_to_name, seal_field):
        frappe.throw(
            _("This record is sealed. Reopen it before attaching a file."),
            title=_("Sealed record"),
        )


def index_file_in_the_record(doc, method=None):
    """``File.after_insert`` - file a record-level upload in the attachments table."""
    if not should_index(doc.attached_to_doctype, doc.attached_to_field):
        return

    if not frappe.db.exists(doc.attached_to_doctype, doc.attached_to_name):
        return

    add_attachment_row(doc.attached_to_doctype, doc.attached_to_name, doc.file_url)


def add_attachment_row(doctype, record, file_url, attachment_type=DEFAULT_TYPE):
    """Append one row through the DocType's own controller.

    ``save()`` is the framework's write path, so the row still passes the controller's rules -
    the duplicate check, the seal guard, the file hash - and the write permission of whoever
    is uploading. Nothing here writes a table directly.
    """
    if not record or not file_url:
        return None

    if row_for(doctype, record, file_url):
        return None

    document = frappe.get_doc(doctype, record)
    document.append(TABLE_FIELD, {"file": file_url, "attachment_type": attachment_type})
    document.save()

    return document.attachments[-1].name


def row_for(doctype, record, file_url):
    """The row already describing this file on this record, if there is one."""
    return frappe.db.get_value(
        TABLE_DOCTYPE,
        {"parent": record, "parenttype": doctype, "file": file_url},
        "name",
    )


def _record_level_files(doctype):
    """Every File attached to this DocType at record level, oldest first."""
    rows = frappe.get_all(
        "File",
        filters={"attached_to_doctype": doctype},
        fields=["attached_to_name", "attached_to_field", "file_url", "file_name"],
        order_by="attached_to_name asc, creation asc",
        limit_page_length=0,
    )

    return [
        row
        for row in rows
        if row["attached_to_name"]
        and not row["attached_to_field"]
        and row["file_url"]
    ]


def plan_indexing():
    """Read-only: what the backfill would create, and what it would leave alone.

    Run it before migrating to see the work:

        bench --site <site> execute murasalat_office.services.attachment_index.plan_indexing

    A sealed record is listed under ``sealed`` and never touched. Its integrity hash covers
    its rows, so adding one would break the seal check on a record nobody tampered with.
    Files uploaded through a field are left to the row the user filled.
    """
    plan = {"create": [], "sealed": [], "already_indexed": [], "orphaned": []}

    for doctype in INDEXED_DOCTYPES:
        seal_field = SEALED_DOCTYPES.get(doctype)

        sealed = (
            set(frappe.get_all(doctype, filters={seal_field: ["is", "set"]}, pluck="name"))
            if seal_field
            else set()
        )

        for row in _record_level_files(doctype):
            record = row["attached_to_name"]
            entry = {
                "doctype": doctype,
                "record": record,
                "file": row["file_url"],
                "file_name": row["file_name"],
            }

            if record in sealed:
                plan["sealed"].append(entry)
            elif not frappe.db.exists(doctype, record):
                plan["orphaned"].append(entry)
            elif row_for(doctype, record, row["file_url"]):
                plan["already_indexed"].append(entry)
            else:
                plan["create"].append(entry)

    return plan


def apply_indexing(plan=None):
    """Create the rows ``plan_indexing`` proposed. Idempotent - safe to run again."""
    plan = plan or plan_indexing()
    created, failed = [], []

    for entry in plan["create"]:
        try:
            row = add_attachment_row(entry["doctype"], entry["record"], entry["file"])
        except Exception:
            failed.append(entry)
            frappe.log_error(
                title="Attachment index backfill",
                message=f"{entry['doctype']} {entry['record']} {entry['file']}\n{frappe.get_traceback()}",
            )
            continue

        if row:
            created.append(entry)
        else:
            failed.append(entry)

    frappe.db.commit()

    return {
        "created": len(created),
        "failed": len(failed),
        "skipped_sealed": len(plan["sealed"]),
        "already_indexed": len(plan["already_indexed"]),
        "orphaned": len(plan["orphaned"]),
    }
