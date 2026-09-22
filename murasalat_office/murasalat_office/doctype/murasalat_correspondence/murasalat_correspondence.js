// Copyright (c) 2026, Murasalat Office and contributors
// For license information, please see license.txt
//
// النظرة الشاملة على المعاملة تظهر أعلى النموذج بمجرد فتحه.
//
// The panel markup is rendered server-side by services/overview.py, so this script is
// only a connector: fetch, inject, and register the native Desk dashboard indicators.
// Every value behind it was read through a permission-aware query.

// Defined defensively here as well as in the referral script, because Desk may load
// either form first and this application ships no bundled asset.
if (typeof window.murasalat_render_overview !== "function") {
    window.murasalat_render_overview = function (frm, method, args, fieldname) {
        const field = frm.get_field(fieldname);
        if (!field || !field.$wrapper) {
            return;
        }

        field.$wrapper.html(
            '<div class="mo-ov"><div class="mo-loading">جارٍ تحميل النظرة الشاملة…</div></div>',
        );

        frappe.call({
            method: method,
            args: args,
            callback(r) {
                if (!r || !r.message) {
                    return;
                }

                field.$wrapper.html(r.message.html || "");

                (r.message.indicators || []).forEach((indicator) => {
                    if (indicator && indicator.label) {
                        frm.dashboard.add_indicator(__(indicator.label), indicator.color);
                    }
                });
            },
            error() {
                field.$wrapper.html(
                    '<div class="mo-ov"><div class="mo-locked">تعذّر تحميل النظرة الشاملة. تحقّق من صلاحياتك ثم أعد تحميل الصفحة.</div></div>',
                );
            },
        });
    };
}

frappe.ui.form.on("Murasalat Correspondence", {
    refresh(frm) {
        if (frm.is_new()) {
            return;
        }

        window.murasalat_render_overview(
            frm,
            "murasalat_office.api.operations.correspondence_overview",
            { correspondence: frm.doc.name },
            "overview_html",
        );

        if (frm.perm[0] && frm.perm[0].create) {
            frm.add_custom_button(
                __("New Referral"),
                () => {
                    frappe.new_doc("Murasalat Referral", {
                        correspondence: frm.doc.name,
                    });
                },
                __("Create"),
            );
        }
    },
});
