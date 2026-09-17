import frappe
from frappe import _


@frappe.whitelist()
def get_governance_health():
    """Expose the read-only governance audit to authorized Desk users."""
    frappe.only_for("System Manager")
    from murasalat_office.services.governance import governance_health
    return governance_health()


@frappe.whitelist()
def verify_record_integrity(correspondence):
    """Explicitly perform the full, attachment-aware integrity verification."""
    from murasalat_office.services.records import verify_integrity
    doc = frappe.get_doc("Murasalat Correspondence", correspondence)
    doc.check_permission("read")
    return {"valid": bool(verify_integrity(doc)), "sealed": bool(doc.integrity_hash)}


@frappe.whitelist()
def operational_summary(correspondence):
    """Read-only projection using native permission-aware Query Builder access."""
    from murasalat_office.services.records import verify_integrity
    doc = frappe.get_doc("Murasalat Correspondence", correspondence)
    doc.check_permission("read")
    referrals = frappe.qb.get_query(
        "Murasalat Referral",
        fields=["name", "due_date", "workflow_state"],
        filters={"correspondence": doc.name},
        ignore_permissions=False,
        order_by="due_date asc",
    ).run(as_dict=True)
    today_date = frappe.utils.getdate(frappe.utils.today())
    overdue_rows = [
        r for r in referrals
        if r.due_date and frappe.utils.getdate(r.due_date) < today_date
    ]
    due_dates = [frappe.utils.getdate(r.due_date) for r in referrals if r.due_date]
    return {
        "name": doc.name,
        "workflow_state": doc.workflow_state,
        "current_holder": doc.current_holder,
        "current_holder_user": doc.current_holder_user,
        "referrals": len(referrals),
        "overdue_referrals": len(overdue_rows),
        "next_due_date": min(due_dates) if due_dates else None,
        "sealed": bool(doc.integrity_hash),
        "integrity_valid": bool(verify_integrity(doc)),
    }
