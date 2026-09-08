app_name = "murasalat_office"
app_title = "Murasalat Office"
app_publisher = "Murasalat Office"
app_description = "Metadata-first correspondence management"
app_email = "admin@example.com"
app_license = "MIT"

fixtures = [
    {"dt": "Role", "filters": [["name", "in", [
        "Murasalat User", "Murasalat Coordinator", "Murasalat Manager",
        "Murasalat Approver", "Murasalat Auditor", "Murasalat Administrator"
    ]]]},
    {"dt": "Permission Type", "filters": [["perm_type", "in", [
        "approve", "withdraw", "reopen", "view_confidential", "download_confidential",
        "receive", "start_referral", "complete_referral", "reject_referral", "return_referral", "close"
    ]]]},
    {"dt": "Workflow", "filters": [["workflow_name", "=", "Murasalat Approval Workflow"]]},
    {"dt": "Workflow State", "filters": [["workflow_state_name", "in", [
        "Draft", "Under Review", "Under Approval", "Approved", "Rejected"
    ]]]}
]

permission_query_conditions = {
    "Murasalat Correspondence": "murasalat_office.security.permissions.get_permission_query_conditions"
}

has_permission = {
    "Murasalat Correspondence": "murasalat_office.security.permissions.has_permission"
}

doctype_js = {
    "Murasalat Correspondence": "public/js/murasalat_correspondence.js"
}

doctype_list_js = {
    "Murasalat Correspondence": "doctype/murasalat_correspondence/murasalat_correspondence_list.js"
}

workflow_methods = [
    {"name": "Murasalat: Mark Under Approval", "method": "murasalat_office.workflow_methods.approval.mark_under_approval"},
    {"name": "Murasalat: Mark Approved", "method": "murasalat_office.workflow_methods.approval.mark_approved"},
    {"name": "Murasalat: Mark Returned", "method": "murasalat_office.workflow_methods.approval.mark_returned"},
    {"name": "Murasalat: Mark Rejected", "method": "murasalat_office.workflow_methods.approval.mark_rejected"}
]

scheduler_events = {
    "daily": [
        "murasalat_office.services.escalation.run_daily_escalation"
    ]
}


after_migrate = [
    "murasalat_office.patches.schema_repair.ensure_child_table_schema",
]
