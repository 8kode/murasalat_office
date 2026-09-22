// Copyright (c) 2026, Murasalat Office and contributors
// For license information, please see license.txt
//
// عوامل تصفية تقادم الإحالات: تاريخ القياس هو أهم عامل — التقادم يُقاس إليه لا إليه اليوم فقط.

frappe.query_reports["Murasalat Referral Aging"] = {
    filters: [
        {
            fieldname: "as_of_date",
            label: __("As Of Date"),
            fieldtype: "Date",
            default: frappe.datetime.get_today(),
            reqd: 1,
        },
        {
            fieldname: "organization",
            label: __("Department"),
            fieldtype: "Link",
            options: "Department",
        },
        {
            fieldname: "user",
            label: __("Recipient User"),
            fieldtype: "Link",
            options: "User",
        },
        {
            fieldname: "importance",
            label: __("Importance"),
            fieldtype: "Link",
            options: "Murasalat Importance Level",
        },
        {
            fieldname: "only_overdue",
            label: __("Only Overdue"),
            fieldtype: "Check",
            default: 0,
        },
    ],
};
