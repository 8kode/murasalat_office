frappe.listview_settings["Murasalat Referral"] = {
    add_fields: [
        "referral_number",
        "correspondence",
        "recipient_type",
        "recipient_organization",
        "recipient_user",
        "due_date",
        "workflow_state",
        "follow_up",
    ],
    hide_name_column: true,
    get_indicator(doc) {
        if (doc.due_date) {
            const today = frappe.datetime.get_today();
            if (doc.due_date < today) return [__("Overdue"), "red", "due_date,<," + today];
            if (doc.due_date === today) return [__("Due Today"), "orange", "due_date,=," + today];
        }
        if (doc.follow_up) return [__("Follow Up"), "blue", "follow_up,=,1"];
        return [__("Scheduled"), "gray", "due_date,is,set"];
    },
};
