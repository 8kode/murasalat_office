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

// ---------------------------------------------------------------------------
// One place to manage attachments.
//
// This form used to offer three ways to attach a file: the attachments table, an
// "Attachment Gallery" field, and Frappe's own attachments panel in the sidebar. Only the
// table records what the file is - its type, where the paper original is filed, whether it
// is secret - and only the table is covered by the integrity seal. The other two are gone:
// the gallery field was removed from the DocType, and the sidebar panel is hidden below.
//
// Uploading stays native. The button opens frappe.ui.FileUploader, the same widget the
// sidebar used, and the uploaded file becomes a row in the table.
// ---------------------------------------------------------------------------

function murasalat_single_attachment_source(frm) {
	// Hide Frappe's own attachments panel, so the table is the only list of files shown.
	const sidebar = frm.sidebar && frm.sidebar.sidebar;

	if (sidebar && sidebar.length) {
		const panel = sidebar.find(".form-attachments");

		if (panel.length) {
			panel.toggle(false);

			const section = panel.closest(".sidebar-section");

			if (section.length) {
				section.toggle(false);
			}
		}
	}

	// A sealed record cannot take new attachments. Say so instead of letting an upload fail
	// validation after the user has already chosen a file.
	if (frm.doc.record_sealed_on) {
		if (!frm.__murasalat_seal_notice) {
			frm.__murasalat_seal_notice = true;
			frm.dashboard.add_indicator(__("مختومة - المرفقات مقفلة"), "green");
		}

		return;
	}

	if (frm.is_new() || !frm.has_perm("write")) {
		return;
	}

	frm.add_custom_button(
		__("رفع مرفق"),
		() => {
			new frappe.ui.FileUploader({
				doctype: frm.doctype,
				docname: frm.docname,
				folder: "Home/Attachments",
				frm: frm,
				on_success: (file_doc) => {
					frm.add_child("attachments", {
						file: file_doc.file_url,
						attachment_type: "Attachment",
					});
					frm.refresh_field("attachments");
					frm.dirty();

					frappe.show_alert({
						message: __("أُضيف المرفق. حدّد نوعه ومجلّده في الجدول."),
						indicator: "green",
					});
				},
			});
		},
		__("المرفقات")
	);
}

frappe.ui.form.on("Murasalat Correspondence", {
	refresh(frm) {
		murasalat_single_attachment_source(frm);
	},
});
