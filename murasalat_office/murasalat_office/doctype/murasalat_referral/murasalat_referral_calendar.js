frappe.views.calendar["Murasalat Referral"] = {
    field_map: {
        start: "due_date",
        end: "due_date",
        id: "name",
        title: "referral_number",
        status: "workflow_state",
    },
    order_by: "due_date",
    get_events_method: "frappe.desk.calendar.get_events",
};
