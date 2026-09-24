"""File the attachments that predate automatic indexing.

Before ``doc_events`` on File existed, only the attachments table recorded a file, so anything
uploaded through the sidebar panel or the gallery was attached to the record without a row.
Those files are already covered by the integrity seal - the hash reads the linked File rows as
well - but they are invisible in the table and carry no type.

Sealed records are left alone on purpose: their stored hash covers their rows, so writing one
would fail the seal check on a record nobody touched. Their files stay covered by the linked
File snapshot.

Run ``plan_indexing`` first to see the work without writing anything:

    bench --site <site> execute murasalat_office.services.attachment_index.plan_indexing

This patch is idempotent - a file that already has a row is skipped - so re-running it after a
partial failure is safe.
"""
import frappe

from murasalat_office.services import attachment_index


def execute():
    plan = attachment_index.plan_indexing()
    summary = attachment_index.apply_indexing(plan)

    print(
        "attachment index: {created} row(s) written, {already_indexed} already indexed, "
        "{skipped_sealed} skipped on sealed records, {orphaned} orphaned, {failed} failed".format(
            **summary
        )
    )

    for entry in plan["create"]:
        print(f"  written: {entry['doctype']} {entry['record']} <- {entry['file_name'] or entry['file']}")

    for entry in plan["sealed"]:
        print(f"  skipped (sealed): {entry['doctype']} {entry['record']} <- {entry['file_name'] or entry['file']}")

    for entry in plan["orphaned"]:
        print(f"  skipped (no such record): {entry['doctype']} {entry['record']} <- {entry['file']}")

    if summary["failed"]:
        frappe.log_error(title="Attachment index backfill", message=str(summary))
