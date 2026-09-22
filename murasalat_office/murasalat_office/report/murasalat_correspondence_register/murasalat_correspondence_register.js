// Copyright (c) 2026, Murasalat Office and contributors
// For license information, please see license.txt
//
// عوامل تصفية سجل المعاملات: تجعله أداة عمل يومية لا جدولًا ثابتًا.

frappe.query_reports["Murasalat Correspondence Register"] = {
    filters: [
        {
            fieldname: "from_date",
            label: __("From Date"),
            fieldtype: "Date",
            default: frappe.datetime.add_months(frappe.datetime.get_today(), -3),
            reqd: 0,
        },
        {
            fieldname: "to_date",
            label: __("To Date"),
            fieldtype: "Date",
            default: frappe.datetime.get_today(),
        },
        {
            fieldname: "correspondence_direction",
            label: __("Direction"),
            fieldtype: "Select",
            options: ["", "Incoming", "Outgoing", "Internal"],
        },
        {
            fieldname: "workflow_state",
            label: __("State"),
            fieldtype: "Data",
        },
        {
            fieldname: "current_holder",
            label: __("Current Holder"),
            fieldtype: "Link",
            options: "Department",
        },
        {
            fieldname: "confidentiality",
            label: __("Confidentiality"),
            fieldtype: "Link",
            options: "Murasalat Confidentiality Level",
        },
        {
            fieldname: "importance",
            label: __("Importance"),
            fieldtype: "Link",
            options: "Murasalat Importance Level",
        },
        {
            fieldname: "sealing",
            label: __("Sealing"),
            fieldtype: "Select",
            options: ["", "Sealed", "Open"],
        },
    ],
};
