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
        # Deprecated field retained only for compatibility with the current
        # schema. It is NOT used to determine personal work ownership.
        "current_holder_user": None,
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