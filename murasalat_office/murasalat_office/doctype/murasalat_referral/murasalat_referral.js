// Copyright (c) 2026, Murasalat Office and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Murasalat Referral", {
// 	refresh(frm) {

// 	},
// });

frappe.ui.form.on("Murasalat Referral", {
    refresh(frm) {
        if (!frm.is_new() && frm.doc.correspondence) {
            frm.add_custom_button(__("Open Correspondence"), () => {
                frappe.set_route(
                    "Form",
                    "Murasalat Correspondence",
                    frm.doc.correspondence,
                );
            }, __("Related"));
        }
    },
});
