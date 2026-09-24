"""Rename the attachment table's free-text folder column to archive_location.

The old column held the name of a Frappe folder while the office read it as "where the paper
original is filed". That collision is what produced values like "dfs" and "نن": everybody
answered a different question. The column is renamed so the code cannot suggest the wrong
meaning again, and its values are carried across rather than dropped - the next patch reports
any that turn out not to be a known location.

Runs before the schema sync, while the old column is still the only one of the two.
"""
import frappe

TABLE = "Murasalat Attachment"
OLD_COLUMN = "folder"
NEW_COLUMN = "archive_location"


def execute():
    print(f"{TABLE}: {OLD_COLUMN} -> {NEW_COLUMN}")

    if not frappe.db.has_column(TABLE, OLD_COLUMN):
        print(f"  {OLD_COLUMN} is not on this site - nothing to rename")
        return

    if frappe.db.has_column(TABLE, NEW_COLUMN):
        print(f"  {NEW_COLUMN} already exists - leaving {OLD_COLUMN} alone")
        return

    column_type = _column_type(OLD_COLUMN) or "varchar(140)"
    frappe.db.sql_ddl(f"alter table `tab{TABLE}` change `{OLD_COLUMN}` `{NEW_COLUMN}` {column_type}")
    print(f"  renamed ({column_type}); values carried across")


def _column_type(column):
    rows = frappe.db.sql(
        """select column_type from information_schema.columns
           where table_schema = database() and table_name = %s and column_name = %s""",
        (f"tab{TABLE}", column),
    )
    return rows[0][0] if rows else None
