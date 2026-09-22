app_name = "murasalat_office"
app_title = "Murasalat Office"
app_publisher = "Murasalat Office"
app_description = "Metadata-first correspondence management"
app_email = "admin@example.com"
app_license = "MIT"


# Roles, permissions and workflows are intentionally not shipped
# as fixtures. Governance remains administered from the
# Frappe/ERPNext Desk UI.
#
# IMPORTANT:
# Native ToDo/Assignment is deliberately NOT hooked here.
# A ToDo assigned from a Murasalat Referral should reference
# the Referral itself. The Referral is the work/routing unit.
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


# There is intentionally no ToDo doc_event hook.
#
# Previous DEV12 behavior tried to infer one
# Murasalat Correspondence.current_holder_user from the latest
# open ToDo linked to the Correspondence. That is ambiguous when
# multiple referrals/assignments exist and also couples assignment
# to write permission on the parent Correspondence.
#
# Native Frappe Assignment should instead be performed on:
#     Murasalat Referral
#
# The Referral identifies the work item; ToDo identifies the user.


after_migrate = [
    "murasalat_office.patches.schema_repair.ensure_child_table_schema",
    "murasalat_office.patches.schema_repair.ensure_membership_unique_index",
]