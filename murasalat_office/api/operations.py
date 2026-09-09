import frappe


@frappe.whitelist()
def verify_record_integrity(correspondence):
    from murasalat_office.services.records import verify_integrity
    doc = frappe.get_doc("Murasalat Correspondence", correspondence)
    doc.check_permission("read")
    return {"valid": bool(verify_integrity(doc)), "sealed": bool(doc.integrity_hash)}


@frappe.whitelist()
def operational_summary(correspondence):
    """Read-only projection with no application-defined workflow states."""
    from murasalat_office.services.records import verify_integrity
    doc = frappe.get_doc("Murasalat Correspondence", correspondence)
    doc.check_permission("read")
    referrals = frappe.get_list(
        "Murasalat Referral",
        filters={"correspondence": doc.name},
        fields=["name", "due_date", "workflow_state"],
        ignore_permissions=False,
        limit_page_length=0,
    )
    overdue_rows = [r for r in referrals if r.due_date and str(r.due_date) < frappe.utils.today()]
    due_dates = [r.due_date for r in referrals if r.due_date]
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
