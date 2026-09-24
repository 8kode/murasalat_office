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
    {
        "name": "Stamp Approval",
        "method": "murasalat_office.services.approvals.stamp_approval",
    },
    {
        "name": "Clear Approval",
        "method": "murasalat_office.services.approvals.clear_approval",
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


# Attachments are indexed from the framework's own File document.
#
# Frappe has one way to attach a file to a document - a File row carrying attached_to_doctype
# and attached_to_name - and every path goes through it: the form's sidebar panel,
# drag-and-drop, the REST upload endpoint, a row's own Attach control. Registering these two
# events is what makes the attachments table the single list of a record's files without
# hiding anything the framework put on the screen.
#
# The rule holds for a sealed correspondence at the framework level, so an upload through the
# REST endpoint is refused exactly like one clicked in the Desk.
doc_events = {
    "File": {
        "before_insert": "murasalat_office.services.attachment_index.refuse_file_on_a_sealed_record",
        "after_insert": "murasalat_office.services.attachment_index.index_file_in_the_record",
    },
}
