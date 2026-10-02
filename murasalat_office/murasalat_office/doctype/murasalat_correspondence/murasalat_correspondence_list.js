// Copyright (c) 2026, Murasalat Office and contributors
// For license information, please see license.txt
//
// مؤشر حالة المعاملة في القائمة: يصف حالة المستند نفسها (مختومة/مغلقة/حالة سير العمل)
// بدل أن يصف تاريخًا لا يعبّر عن حالة المعاملة.

frappe.listview_settings["Murasalat Correspondence"] = {
    add_fields: [
        "subject",
        "correspondence_direction",
        "workflow_state",
        "confidentiality",
        "importance",
        "due_date",
        "closed_on",
        "record_sealed_on",
        "current_holder",
    ],
    hide_name_column: true,

    get_indicator(doc) {
        // الأخصّ أولًا: الختم يعلو على أي حالة أخرى.
        if (doc.record_sealed_on) {
            return [__("Sealed"), "green", "record_sealed_on,is,set"];
        }

        if (doc.closed_on) {
            return [__("Closed"), "gray", "closed_on,is,set"];
        }

        const state = (doc.workflow_state || "").trim();

        // Workflow is site-defined. Display the actual state chosen in Desk without
        // mapping or naming any application-owned states.
        if (state) {
            return [__(state), "blue", "workflow_state,=," + state];
        }

        return [__("Workflow not set"), "gray", "workflow_state,is,not set"];
    },
};
