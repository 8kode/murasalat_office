import frappe
from frappe import _
from frappe.utils import now_datetime
from murasalat_office.services.delegation import can_act_for
from murasalat_office.services.organization_context import get_active_organization

OPEN = {"Pending", "Sent", "Received", "In Progress", "Overdue"}
TERMINAL = {"Completed", "Rejected", "Returned", "Withdrawn", "Cancelled"}
TRANSITIONS = {
    "receive": {"Pending", "Sent", "Overdue"},
    "start": {"Received", "Overdue"},
    "complete": {"Received", "In Progress", "Overdue"},
    "reject": {"Pending", "Sent", "Overdue"},
    "return": OPEN,
}
PERMISSION_FOR_ACTION = {
    "receive": "receive", "start": "start_referral", "complete": "complete_referral",
    "reject": "reject_referral", "return": "return_referral",
}

def _get(name):
    doc = frappe.get_doc("Murasalat Correspondence", name)
    doc.check_permission("read")
    return doc

def _referral(doc, referral_number):
    for row in doc.referrals or []:
        if row.referral_number == referral_number:
            return row
    frappe.throw(_("Referral not found."))

def _require_permission(doc, action):
    perm = PERMISSION_FOR_ACTION.get(action)
    if perm and not frappe.has_permission(doc.doctype, perm, doc=doc):
        frappe.throw(_("You do not have permission for action: {0}").format(action), frappe.PermissionError)

def _check_actor(row, action=None):
    user = frappe.session.user
    if user == "Administrator":
        return {"acting_for": None, "delegation": None}
    if row.recipient_type == "User":
        result = can_act_for(row.recipient_user, user, None, action)
        if result.get("authorized"):
            return result
    elif row.recipient_type == "Organization":
        active_org = get_active_organization(user, require=True)
        if active_org == row.recipient_organization:
            return {"acting_for": None, "delegation": None}
    frappe.throw(_("You are not authorized to act on this referral."), frappe.PermissionError)

def _append(doc, activity_type, row=None, details=None, acting_for=None, delegation=None):
    doc.append("activities", {
        "activity_type": activity_type,
        "activity_on": now_datetime(),
        "actor": frappe.session.user,
        "acting_for": acting_for,
        "delegation": delegation,
        "organization": getattr(row, "recipient_organization", None) if row else doc.current_holder,
        "referral_number": getattr(row, "referral_number", None) if row else None,
        "details": details or "",
    })

def _sync_todo(row, status):
    if not row.referral_todo or not frappe.db.exists("ToDo", row.referral_todo):
        return
    todo = frappe.get_doc("ToDo", row.referral_todo)
    target = "Closed" if status == "Completed" else "Cancelled" if status in TERMINAL else None
    if target and todo.status != target:
        todo.status = target
        todo.save(ignore_permissions=True)

def _save(doc):
    doc.flags.murasalat_operation = True
    doc.save()
    return {"name": doc.name, "status": doc.status}

def _transition(correspondence, referral_number, action, target_status, note=None, required_note=False):
    if required_note and not note:
        frappe.throw(_("A reason is required."))
    doc = _get(correspondence)
    _require_permission(doc, action)
    row = _referral(doc, referral_number)
    if row.status not in TRANSITIONS[action]:
        frappe.throw(_("Invalid referral state transition from {0} using {1}.").format(row.status, action))
    actor_ctx = _check_actor(row, action)
    row.status = target_status
    if action == "receive": row.received_on = now_datetime(); row.received_by = frappe.session.user
    if action == "complete": row.completed_on = now_datetime(); row.completed_by = frappe.session.user
    if action == "complete":
        open_rows = [r for r in doc.referrals or [] if r.name != row.name and r.status in OPEN]
        doc.status = "Completed" if not open_rows else "In Progress"
    elif target_status == "Received": doc.status = "Received"
    elif target_status == "In Progress": doc.status = "In Progress"
    _sync_todo(row, target_status)
    labels={"receive":"Referral Received","start":"Referral Started","complete":"Referral Completed","reject":"Referral Rejected","return":"Referral Returned"}
    _append(doc, labels[action], row, note or labels[action], **actor_ctx)
    return _save(doc)

@frappe.whitelist()
def receive(correspondence, referral_number, note=None): return _transition(correspondence, referral_number, "receive", "Received", note)
@frappe.whitelist()
def start(correspondence, referral_number, note=None): return _transition(correspondence, referral_number, "start", "In Progress", note)
@frappe.whitelist()
def complete(correspondence, referral_number, note=None): return _transition(correspondence, referral_number, "complete", "Completed", note)
@frappe.whitelist()
def reject(correspondence, referral_number, reason): return _transition(correspondence, referral_number, "reject", "Rejected", reason, True)
@frappe.whitelist()
def return_referral(correspondence, referral_number, reason): return _transition(correspondence, referral_number, "return", "Returned", reason, True)

@frappe.whitelist()
def withdraw(correspondence, reason):
    if not reason: frappe.throw(_("A withdrawal reason is required."))
    doc = _get(correspondence)
    if not frappe.has_permission(doc.doctype, "withdraw", doc=doc): frappe.throw(_("Not permitted."), frappe.PermissionError)
    if doc.status in {"Closed", "Completed", "Withdrawn"}: frappe.throw(_("This correspondence cannot be withdrawn in its current state."))
    for row in doc.referrals or []:
        if row.status in OPEN: row.status = "Withdrawn"; _sync_todo(row, "Withdrawn")
    doc.status = "Withdrawn"; _append(doc, "Withdrawn", details=reason)
    return _save(doc)

@frappe.whitelist()
def reopen(correspondence, reason):
    if not reason: frappe.throw(_("A reopen reason is required."))
    doc = _get(correspondence)
    if not frappe.has_permission(doc.doctype, "reopen", doc=doc): frappe.throw(_("Not permitted."), frappe.PermissionError)
    if doc.status not in {"Closed", "Completed", "Rejected", "Withdrawn"}: frappe.throw(_("Only terminal correspondence can be reopened."))
    doc.status = "Reopened"; doc.closed_on = None; _append(doc, "Reopened", details=reason)
    return _save(doc)

@frappe.whitelist()
def close(correspondence, note=None):
    doc = _get(correspondence)
    if not frappe.has_permission(doc.doctype, "close", doc=doc): frappe.throw(_("Not permitted."), frappe.PermissionError)
    if any(r.status in OPEN for r in doc.referrals or []): frappe.throw(_("All active referrals must be resolved before closing."))
    doc.status = "Closed"; doc.closed_on = now_datetime(); _append(doc, "Closed", details=note or "Correspondence closed.")
    return _save(doc)


@frappe.whitelist()
def verify_record_integrity(correspondence):
    from murasalat_office.services.records import verify_integrity
    doc = frappe.get_doc("Murasalat Correspondence", correspondence)
    if not doc.has_permission("read"):
        frappe.throw("Not permitted", frappe.PermissionError)
    return {"valid": bool(verify_integrity(doc)), "sealed": bool(doc.integrity_hash)}


@frappe.whitelist()
def operational_summary(correspondence):
    """Return a permission-checked, read-only operational snapshot for UI/Workspace use."""
    doc = _get(correspondence)
    open_rows = [r for r in (doc.referrals or []) if r.status in OPEN]
    overdue_rows = [r for r in open_rows if r.status == "Overdue"]
    due_dates = [r.due_date for r in open_rows if r.due_date]
    return {
        "name": doc.name,
        "status": doc.status,
        "current_holder": doc.current_holder,
        "current_holder_user": doc.current_holder_user,
        "open_referrals": len(open_rows),
        "overdue_referrals": len(overdue_rows),
        "next_due_date": min(due_dates) if due_dates else None,
        "sealed": bool(doc.integrity_hash),
        "integrity_valid": bool(verify_record_integrity(correspondence).get("valid")),
    }
