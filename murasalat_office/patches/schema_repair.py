import frappe


CHILD_TABLES = (
    "Murasalat Attachment",
    "Murasalat Correspondence Activity",
    "Murasalat Correspondence Link",
    "Murasalat Referral",
)


def _table_exists(table: str) -> bool:
    return bool(frappe.db.sql("SHOW TABLES LIKE %s", table))


def ensure_child_table_schema():
    """Repair legacy child tables without breaking migrate.

    This hook runs after Frappe has synchronized DocTypes. It uses physical-table
    checks because frappe.db.has_column/add_column expect a DocType name rather
    than a fully-qualified SQL table name (``tab...``).
    """
    for doctype in CHILD_TABLES:
        if not frappe.db.exists("DocType", doctype):
            continue

        table = f"tab{doctype}"
        if not _table_exists(table):
            frappe.log_error(
                title="Murasalat child table missing after schema sync",
                message=f"Expected child table `{table}` for DocType `{doctype}` was not found. Skipping legacy repair.",
            )
            continue

        existing = {row[0] for row in frappe.db.sql(f"SHOW COLUMNS FROM `{table}`")}
        columns = {
            "parent": "varchar(140)",
            "parenttype": "varchar(140)",
            "parentfield": "varchar(140)",
        }

        for column, sql_type in columns.items():
            if column not in existing:
                frappe.db.sql(f"ALTER TABLE `{table}` ADD COLUMN `{column}` {sql_type}")

        try:
            indexes = {row[2] for row in frappe.db.sql(f"SHOW INDEX FROM `{table}`")}
            if "parent" not in indexes:
                frappe.db.sql(f"ALTER TABLE `{table}` ADD INDEX `parent` (`parent`)")
        except Exception:
            # Index creation is an optimization and must never make migrate fail.
            pass
