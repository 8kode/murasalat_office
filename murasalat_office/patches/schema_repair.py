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


def ensure_membership_unique_index():
    """Enforce one active membership row per user/organization pair at DB level.

    The controller still performs a friendly duplicate check, while this unique
    index closes the concurrent-insert race. Existing duplicate data is never
    deleted automatically; index creation is logged for administrator remediation.
    """
    doctype = "Murasalat User Organization Membership"
    if not frappe.db.exists("DocType", doctype) or not frappe.db.table_exists(doctype):
        return

    try:
        index_exists = frappe.db.multisql(
            {
                "mariadb": (
                    "SELECT 1 FROM information_schema.statistics "
                    "WHERE table_schema = DATABASE() AND table_name = %s AND index_name = %s LIMIT 1"
                ),
                "postgres": (
                    "SELECT 1 FROM pg_indexes WHERE schemaname = current_schema() AND indexname = %s LIMIT 1"
                ),
            },
            ("tabMurasalat User Organization Membership", "murasalat_user_org_unique_idx") if frappe.db.db_type == "mariadb" else ("murasalat_user_org_unique_idx",),
        )
        if index_exists:
            return

        frappe.db.multisql(
            {
                "mariadb": (
                    "ALTER TABLE `tabMurasalat User Organization Membership` "
                    "ADD UNIQUE INDEX `murasalat_user_org_unique_idx` (`user`, `organization`)"
                ),
                "postgres": (
                    'CREATE UNIQUE INDEX "murasalat_user_org_unique_idx" '
                    'ON "tabMurasalat User Organization Membership" ("user", "organization")'
                ),
            }
        )
    except Exception:
        # Existing indexes and legacy duplicate data are both safe to leave in place;
        # neither should make bench migrate fail. Administrators can remediate any
        # duplicate rows reported by the error log and rerun migrate.
        frappe.log_error(
            title="Murasalat membership unique index not created",
            message=(
                "The composite unique index on user/organization could not be created. "
                "This may indicate an existing index or duplicate legacy rows. "
                "Review the site database before enabling concurrent membership writes."
            ),
        )
