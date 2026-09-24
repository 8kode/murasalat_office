"""Give the attachment table its vocabulary, and reconcile what it already holds.

Runs after the schema sync, so both master tables exist. Two jobs, in this order:

1. Seed the attachment types and archive locations (idempotent - see setup/master_data.py).
   The three types already stored on records are among the seeded codes, so existing rows keep
   resolving without a data migration.
2. Report - and clear - any value that resolves to nothing. A Link field is validated on save,
   so a value pointing at a record that does not exist would block the very next save of that
   correspondence. Every cleared row is printed with its parent, so nothing is quietly lost:
   re-file it by hand against the right location.

An unknown attachment type is reset to ``Attachment`` rather than cleared, because the field is
mandatory and ``Attachment`` is the generic code that means "an accompanying paper".
"""
import frappe

from murasalat_office.setup import master_data

TABLE = "Murasalat Attachment"
DEFAULT_TYPE = "Attachment"


def execute():
    report = master_data.seed()
    print("attachment vocabulary: %d created, %d already present" % (
        len(report["created"]), len(report["exists"])))

    for entry in report["created"]:
        if entry["doctype"] in ("Murasalat Attachment Type", "Murasalat Archive Location"):
            print("  created: %s %s" % (entry["doctype"], entry["name"]))

    _clear_unknown_locations()
    _reset_unknown_types()

    for missing in report["missing_required"]:
        print("  MISSING, needed by a field default: %s %s" % (missing["doctype"], missing["name"]))


def _rows(fieldname):
    rows = frappe.get_all(
        TABLE,
        filters={fieldname: ["is", "set"]},
        fields=["name", "parent", "parenttype", fieldname],
    )
    return [row for row in rows if row[fieldname]]


def _clear_unknown_locations():
    known = set(frappe.get_all("Murasalat Archive Location", pluck="name"))
    unknown = [row for row in _rows("archive_location") if row["archive_location"] not in known]

    if not unknown:
        print("archive locations: every value resolves")
        return

    for row in unknown:
        print("  cleared: %s %s held %r, which is not a known location" % (
            row["parenttype"], row["parent"], row["archive_location"]))
        frappe.db.set_value(TABLE, row["name"], "archive_location", None, update_modified=False)

    frappe.db.commit()
    print("archive locations: %d value(s) cleared - re-file those rows by hand" % len(unknown))


def _reset_unknown_types():
    known = set(frappe.get_all("Murasalat Attachment Type", pluck="name"))
    unknown = [row for row in _rows("attachment_type") if row["attachment_type"] not in known]

    if not unknown:
        print("attachment types: every value resolves")
        return

    for row in unknown:
        print("  reset: %s %s held unknown type %r -> %s" % (
            row["parenttype"], row["parent"], row["attachment_type"], DEFAULT_TYPE))
        frappe.db.set_value(TABLE, row["name"], "attachment_type", DEFAULT_TYPE, update_modified=False)

    frappe.db.commit()
    print("attachment types: %d value(s) reset" % len(unknown))
