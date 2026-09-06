from __future__ import annotations

import frappe


REFERRAL_STATE_MAP = {
    "Draft": "Murasalat Referral Draft",
    "Sent": "Murasalat Referral Sent",
    "Received": "Murasalat Referral Received",
    "In Progress": "Murasalat Referral In Progress",
    "Completed": "Murasalat Referral Completed",
    "Returned": "Murasalat Referral Returned",
    "Withdrawn": "Murasalat Referral Withdrawn",
    "Cancelled": "Murasalat Referral Cancelled",
}


def execute():
    frappe.delete_doc_if_exists("Client Script", "Set Owner Department Automatically")

    if frappe.db.has_column("tabMurasalat Referral", "status"):
        for old_state, new_state in REFERRAL_STATE_MAP.items():
            frappe.db.sql(
                """
                UPDATE `tabMurasalat Referral`
                SET workflow_state = %s
                WHERE (workflow_state IS NULL OR workflow_state = '')
                  AND status = %s
                """,
                (new_state, old_state),
            )

    frappe.db.sql(
        """
        UPDATE `tabMurasalat Referral`
        SET workflow_state = 'Murasalat Referral Draft'
        WHERE workflow_state IS NULL OR workflow_state = ''
        """
    )

    frappe.db.sql(
        """
        UPDATE `tabMurasalat Correspondence`
        SET correspondence_number = name
        WHERE docstatus = 1
          AND (correspondence_number IS NULL OR correspondence_number = '')
        """
    )

    frappe.db.sql(
        """
        UPDATE `tabMurasalat Correspondence`
        SET barcode = correspondence_number,
            qr_code = correspondence_number
        WHERE correspondence_number IS NOT NULL
          AND correspondence_number != ''
        """
    )

    frappe.db.commit()
