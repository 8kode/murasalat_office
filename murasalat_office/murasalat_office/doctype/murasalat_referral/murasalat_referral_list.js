// Copyright (c) 2026, Murasalat Office and contributors
// For license information, please see license.txt
//
// مؤشر الإحالة في القائمة: يرتّب الأهمية تشغيليًا — مكتملة، ثم مسوّدة لم تُرسل،
// ثم متأخرة، ثم تستحق اليوم، ثم للمتابعة، ثم مفتوحة.

frappe.listview_settings["Murasalat Referral"] = {
    add_fields: [
        "referral_number",
        "correspondence",
        "recipient_type",
        "recipient_department",
        "recipient_user",
        "due_date",
        "sent_on",
        "completed_on",
        "workflow_state",
        "follow_up",
    ],
    hide_name_column: true,

    get_indicator(doc) {
        if (doc.completed_on) {
            return [__("Completed"), "green", "completed_on,is,set"];
        }

        // إحالة لم تُرسل بعد: ليست عملًا جاريًا لأحد.
        if (!doc.sent_on) {
            return [__("Draft — Not Sent"), "orange", "sent_on,is,not set"];
        }

        const today = frappe.datetime.get_today();

        if (doc.due_date) {
            if (doc.due_date < today) {
                return [__("Overdue"), "red", "due_date,<," + today];
            }
            if (doc.due_date === today) {
                return [__("Due Today"), "orange", "due_date,=," + today];
            }
        }

        if (doc.follow_up) {
            return [__("Follow Up"), "blue", "follow_up,=,1"];
        }

        return [__("Open"), "blue", "sent_on,is,set"];
    },
};
