// Copyright (c) 2026, Murasalat Office and contributors
// For license information, please see license.txt
//
// النظرة الشاملة على الإحالة تظهر أعلى النموذج بمجرد فتحه: طوابع دورة الحياة،
// والتعليمات، والمعاملة المرجعية، وبقية إحالات المعاملة، ومسار هذه الإحالة.
//
// The panel markup is rendered server-side by services/overview.py.

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

frappe.ui.form.on("Murasalat Referral", {
    refresh(frm) {
        if (frm.is_new()) {
            return;
        }

        window.murasalat_render_overview(
            frm,
            "murasalat_office.api.operations.referral_overview",
            { referral: frm.doc.name },
            "overview_html",
        );

        if (frm.doc.correspondence) {
            frm.add_custom_button(
                __("Open Correspondence"),
                () => {
                    frappe.set_route(
                        "Form",
                        "Murasalat Correspondence",
                        frm.doc.correspondence,
                    );
                },
                __("Related"),
            );
        }
    },
});
