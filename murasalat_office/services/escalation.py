import frappe
from frappe.utils import add_days, getdate, now_datetime

OPEN_STATES = {"Pending", "Sent", "Received", "In Progress", "Overdue"}


def _notify(user, subject, document, referral_number):
    if not user:
        return
    frappe.get_doc({
        "doctype": "Notification Log",
        "for_user": user,
        "type": "Alert",
        "subject": subject,
        "document_type": document.doctype,
        "document_name": document.name,
        "from_user": frappe.session.user or "Administrator",
        "email_content": f"{subject} | Referral: {referral_number}",
    }).insert(ignore_permissions=True)


def run_daily_escalation():
    policy = frappe.get_single("Murasalat Escalation Policy")
    if not policy.enabled:
        return {"processed": 0, "events": 0}

    today = getdate()
    processed = events = 0
    names = frappe.get_all("Murasalat Correspondence", pluck="name")
    for name in names:
        doc = frappe.get_doc("Murasalat Correspondence", name)
        changed = False
        for row in doc.referrals or []:
            if row.status not in OPEN_STATES or not row.due_date:
                continue
            processed += 1
            due = getdate(row.due_date)
            recipient = row.recipient_user

            if policy.reminder_days_before is not None and not row.reminder_sent_on:
                reminder_date = add_days(due, -int(policy.reminder_days_before or 0))
                if today >= reminder_date and today <= due:
                    _notify(recipient, f"Correspondence due soon: {doc.subject}", doc, row.referral_number)
                    row.reminder_sent_on = now_datetime(); changed = True; events += 1

            if today > due and row.status != "Overdue":
                row.status = "Overdue"; changed = True

            overdue_days = (today - due).days
            manager_after = int(policy.manager_escalation_days_after or 0)
            if manager_after > 0 and overdue_days >= manager_after and policy.manager_user and not row.manager_escalated_on:
                _notify(policy.manager_user, f"Overdue correspondence: {doc.subject}", doc, row.referral_number)
                row.manager_escalated_on = now_datetime(); changed = True; events += 1

            final_after = int(policy.final_escalation_days_after or 0)
            if final_after > 0 and overdue_days >= final_after and policy.final_user and not row.final_escalated_on:
                _notify(policy.final_user, f"Critical overdue correspondence: {doc.subject}", doc, row.referral_number)
                row.final_escalated_on = now_datetime(); changed = True; events += 1

        if changed:
            doc.flags.murasalat_operation = True
            doc.save(ignore_permissions=True)
            frappe.db.commit()
    return {"processed": processed, "events": events}
