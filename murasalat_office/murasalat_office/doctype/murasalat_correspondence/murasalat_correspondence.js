// Copyright (c) 2026, Murasalat Office and contributors
// For license information, please see license.txt

frappe.ui.form.on("Murasalat Correspondence", {
    refresh(frm) {
        if (frm.is_new() || !frm.perm[0]?.create) {
            return;
        }

        frm.add_custom_button(__("New Referral"), () => {
            frappe.new_doc("Murasalat Referral", {
                correspondence: frm.doc.name,
            });
        }, __("Create"));
    },
});