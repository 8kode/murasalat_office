import json

import frappe


FIELDS = (
    "referral_number", "recipient_type", "recipient_organization", "recipient_user",
    "direction", "importance", "due_date", "instructions", "private_referral",
    "paper_copy", "cc_copy", "follow_up", "sent_on", "received_by", "received_on",
    "completed_by", "completed_on",
)


def execute():
    """Convert legacy child referral rows in place to standalone Referral documents."""
    if not frappe.db.exists("DocType", "Murasalat Referral"):
        return

    table = "tabMurasalat Referral"
    try:
        columns = {r[0] for r in frappe.db.sql(f"SHOW COLUMNS FROM `{table}`")}
    except Exception:
        return

    if "parent" not in columns or "parenttype" not in columns:
        return

    rows = frappe.db.sql(
        f"SELECT * FROM `{table}` WHERE parenttype=%s",
        ("Murasalat Correspondence",),
        as_dict=True,
    )
    for row in rows:
        if not row.get("parent") or not frappe.db.exists("Murasalat Correspondence", row.parent):
            continue

        values = {field: row.get(field) for field in FIELDS if field in columns}
        legacy = {
            field: row.get(field)
            for field in ("status", "referral_todo", "reminder_sent_on", "manager_escalated_on", "final_escalated_on")
            if field in columns and row.get(field) is not None
        }
        values.update({
            "correspondence": row.parent,
            "workflow_state": row.get("status"),
            "legacy_history": json.dumps(legacy, default=str, ensure_ascii=False, sort_keys=True),
        })
        # The table is the same physical table after the child->standalone conversion.
        # Convert each row in place instead of inserting a duplicate primary key.
        frappe.db.set_value("Murasalat Referral", row.name, values, update_modified=False)
