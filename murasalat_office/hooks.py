app_name = "murasalat_office"
app_title = "Murasalat Office"
app_publisher = "Murasalat Office"
app_description = "Metadata-first correspondence management"
app_email = "admin@example.com"
app_license = "MIT"

# Roles, permissions and workflows are intentionally not shipped as fixtures.
# All governance is administered from the Frappe/ERPNext Desk UI.







after_migrate = [
    "murasalat_office.patches.schema_repair.ensure_child_table_schema",
    "murasalat_office.patches.schema_repair.ensure_membership_unique_index",
]
