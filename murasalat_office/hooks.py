app_name = "murasalat_office"
app_title = "Murasalat Office"
app_publisher = "Murasalat Office"
app_description = "Metadata-first correspondence management"
app_email = "admin@example.com"
app_license = "MIT"


# Roles, permissions and workflows are intentionally not shipped
# as fixtures. All governance is administered from the Frappe/ERPNext
# Desk UI.

workflow_methods = [
    {
        "name": "Register Correspondence",
        "method": "murasalat_office.services.lifecycle.register_correspondence",
    },
    {
        "name": "Close Correspondence",
        "method": "murasalat_office.services.lifecycle.close_correspondence",
    },
    {
        "name": "Seal Correspondence",
        "method": "murasalat_office.services.lifecycle.seal_correspondence",
    },
    {
        "name": "Reopen Correspondence",
        "method": "murasalat_office.services.lifecycle.reopen_correspondence",
    },
    
    {
        "name": "Send Referral",
        "method": "murasalat_office.services.lifecycle.send_referral",
    },
    {
        "name": "Receive Referral",
        "method": "murasalat_office.services.lifecycle.receive_referral",
    },
    {
        "name": "Complete Referral",
        "method": "murasalat_office.services.lifecycle.complete_referral",
    },
]


# Native Frappe Assignment works through ToDo records.
# These events synchronize the explicit current_holder_user
# projection on Murasalat Correspondence.
doc_events = {
    "ToDo": {
        "after_insert": (
            "murasalat_office.services.lifecycle." "sync_current_holder_user"
        ),
        "on_update": (
            "murasalat_office.services.lifecycle." "sync_current_holder_user"
        ),
        "on_trash": ("murasalat_office.services.lifecycle." "sync_current_holder_user"),
    },
}


after_migrate = [
    "murasalat_office.patches.schema_repair.ensure_child_table_schema",
    "murasalat_office.patches.schema_repair.ensure_membership_unique_index",
]
