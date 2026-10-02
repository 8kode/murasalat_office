import frappe


CHILD_TABLES = (
    "Murasalat Attachment",
    "Murasalat Correspondence Activity",
    "Murasalat Correspondence Link",
)


def _add_column(doctype, column):
    table = f"tab{doctype}"
    frappe.db.multisql(
        {
            "mariadb": f"ALTER TABLE `{table}` ADD COLUMN `{column}` varchar(140)",
            "postgres": f'ALTER TABLE "{table}" ADD COLUMN "{column}" varchar(140)',
        }
    )


def ensure_child_table_schema():
    """Repair legacy child-table columns/indexes using cross-database Frappe APIs."""
    for doctype in CHILD_TABLES:
        if not frappe.db.exists("DocType", doctype):
            continue
        try:
            if not frappe.db.table_exists(doctype):
                frappe.log_error(
                    title="Murasalat child table missing after schema sync",
                    message=f"Expected child table for DocType `{doctype}` was not found. Skipping legacy repair.",
                )
                continue

            existing = set(frappe.db.get_table_columns(doctype))
            for column in ("parent", "parenttype", "parentfield"):
                if column not in existing:
                    _add_column(doctype, column)

            try:
                frappe.db.add_index(doctype, ["parent"], index_name="murasalat_child_parent_idx")
            except Exception:
                # Index creation is an optimization and must never block migrate.
                pass
        except Exception:
            # Schema repair is deliberately defensive: a legacy site should remain
            # migratable even when an already-correct table needs no repair.
            frappe.log_error(
                title="Murasalat child table schema repair failed",
                message=f"Unable to inspect/repair legacy child table for `{doctype}`.",
            )

