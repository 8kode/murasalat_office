frappe.listview_settings["Murasalat Correspondence"] = {
    add_fields: [
        "subject",
        "correspondence_type",
        "workflow_state",
        "confidentiality",
        "importance",
        "due_date",
        "current_holder_user",
    ],
    hide_name_column: true,
    get_indicator(doc) {
        if (!doc.due_date) return [__("No Due Date"), "gray", "due_date,is,set"];
        const today = frappe.datetime.get_today();
        if (doc.due_date < today) return [__("Overdue"), "red", "due_date,<," + today];
        if (doc.due_date === today) return [__("Due Today"), "orange", "due_date,=," + today];
        return [__("Scheduled"), "blue", "due_date,>," + today];
    },
};
