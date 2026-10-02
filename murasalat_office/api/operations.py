import frappe
from frappe import _

from murasalat_office.services.lifecycle import OPEN_REFERRAL_FILTERS


@frappe.whitelist()
def get_governance_health():
    """Expose the read-only governance audit to System Managers."""
    frappe.only_for("System Manager")

    from murasalat_office.services.governance import governance_health

    return governance_health()


@frappe.whitelist()
def verify_record_integrity(correspondence):
    """Perform the explicit, attachment-aware integrity verification."""
    from murasalat_office.services.records import verify_integrity

    doc = frappe.get_doc(
        "Murasalat Correspondence",
        correspondence,
    )
    doc.check_permission("read")

    return {
        "valid": bool(
            verify_integrity(
                doc,
                verify_files=True,
            )
        ),
        "sealed": bool(doc.integrity_hash),
    }


@frappe.whitelist()
def operational_summary(correspondence):
    """Return a permission-aware operational summary.

    The overdue count represents OPEN referrals only.
    Full attachment hashing is intentionally not performed here because this
    endpoint is an operational dashboard, not an explicit integrity audit.
    """
    from murasalat_office.services.records import verify_integrity

    doc = frappe.get_doc(
        "Murasalat Correspondence",
        correspondence,
    )
    doc.check_permission("read")

    referrals = frappe.qb.get_query(
        "Murasalat Referral",
        fields=[
            "name",
            "due_date",
            "workflow_state",
            "completed_on",
            "recipient_type",
            "recipient_department",
            "recipient_user",
        ],
        filters=[
            ["correspondence", "=", doc.name],
            *OPEN_REFERRAL_FILTERS,
        ],
        ignore_permissions=False,
        order_by="due_date asc, modified desc",
    ).run(as_dict=True)

    today_date = frappe.utils.getdate(
        frappe.utils.today()
    )

    open_with_due_date = [
        row
        for row in referrals
        if row.due_date
    ]

    overdue_rows = [
        row
        for row in open_with_due_date
        if frappe.utils.getdate(row.due_date) < today_date
    ]

    due_dates = [
        frappe.utils.getdate(row.due_date)
        for row in open_with_due_date
    ]

    return {
        "name": doc.name,
        "workflow_state": doc.workflow_state,
        "current_holder": doc.current_holder,
        "open_referrals": len(referrals),
        "overdue_referrals": len(overdue_rows),
        "next_due_date": min(due_dates) if due_dates else None,
        "sealed": bool(doc.integrity_hash),
        "integrity_valid": bool(
            verify_integrity(
                doc,
                verify_files=False,
            )
        ),
        "integrity_check_scope": "record_snapshot_only",
    }


@frappe.whitelist()
def correspondence_overview(correspondence):
    """Read-only overview panel for one correspondence.

    The panel markup is rendered server-side so it can be tested; access is decided by
    services.overview, which reads through permission-aware queries only.
    """
    from murasalat_office.services.overview import correspondence_overview as build

    return build(correspondence)


@frappe.whitelist()
def referral_overview(referral):
    """Read-only overview panel for one referral, including its own lifecycle trail."""
    from murasalat_office.services.overview import referral_overview as build

    return build(referral)


@frappe.whitelist()
def get_reply_context(correspondence):
    """Return the permission-aware context used by the native Create Reply dialog."""
    from murasalat_office.services.reply import get_reply_context as build

    return build(correspondence)


@frappe.whitelist()
def create_reply_draft(
    correspondence, subject=None, notes=None, source_department=None, salutation=None,
    closing_phrase=None, signatory_name=None, signatory_position=None, approval_entity=None,
    preparation_entity=None, prepared_on=None,
):
    """Create a new Outgoing correspondence as a draft reply to an Incoming record."""
    from murasalat_office.services.reply import create_reply_draft as create

    return create(
        correspondence=correspondence,
        subject=subject,
        notes=notes,
        source_department=source_department,
        salutation=salutation,
        closing_phrase=closing_phrase,
        signatory_name=signatory_name,
        signatory_position=signatory_position,
        approval_entity=approval_entity,
        preparation_entity=preparation_entity,
        prepared_on=prepared_on,
    )
