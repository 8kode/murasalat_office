import json

import frappe


LEGACY_FIELDS = (
    "status",
    "referral_todo",
    "reminder_sent_on",
    "manager_escalated_on",
    "final_escalated_on",
)


def execute():
    """Repair/complete the child-to-standalone conversion and preserve legacy fields."""
    if not frappe.db.exists("DocType", "Murasalat Referral"):
        return

    table = "tabMurasalat Referral"
    columns = {row[0] for row in frappe.db.sql(f"SHOW COLUMNS FROM `{table}`")}
    if "parent" not in columns or "parenttype" not in columns:
        return

    available = [field for field in LEGACY_FIELDS if field in columns]
    rows = frappe.db.sql(
        f"SELECT * FROM `{table}` WHERE parenttype=%s",
        ("Murasalat Correspondence",),
        as_dict=True,
    )
    for row in rows:
        if not row.get("parent") or not frappe.db.exists("Murasalat Correspondence", row.parent):
            continue

        values = {"correspondence": row.parent}
        if "workflow_state" in columns and row.get("status") is not None:
            values["workflow_state"] = row.get("status")
        if "legacy_history" in columns:
            legacy = {field: row.get(field) for field in available if row.get(field) is not None}
            if legacy and not row.get("legacy_history"):
                values["legacy_history"] = json.dumps(legacy, default=str, ensure_ascii=False, sort_keys=True)
        frappe.db.set_value("Murasalat Referral", row.name, values, update_modified=False)
