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

// ---------------------------------------------------------------------------
// Attachments.
//
// Frappe has one way to attach a file to a document - a File row carrying
// attached_to_doctype and attached_to_name. This sidebar panel, drag-and-drop, the REST
// endpoint and a row's own Attach control all go through it, and the app registers a File
// event server-side that files a record-level upload in the attachments table. So the panel
// is left exactly as the framework built it: it uploads natively, and the table describes
// what was uploaded. Nothing here hides framework markup.
//
// A sealed correspondence refuses the file in File.before_insert, not here. The indicator
// below only says so before somebody picks a file and waits for an upload to fail.
// ---------------------------------------------------------------------------

function murasalat_attachment_rules(frm) {
	// A file attached from the panel is filed in the table server-side, so the table has to
	// be re-read for the new row to appear. on_success is delegated to, never replaced.
	if (frm.attachments && !frm.__murasalat_attach_hooked) {
		frm.__murasalat_attach_hooked = true;

		const native_on_success = frm.attachments.on_success;

		frm.attachments.on_success = (...args) => {
			if (native_on_success) {
				native_on_success(...args);
			}

			frm.reload_doc();
		};
	}
}

frappe.ui.form.on("Murasalat Referral", {
	refresh(frm) {
		murasalat_attachment_rules(frm);
	},
});
