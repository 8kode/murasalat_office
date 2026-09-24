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
// attached_to_doctype and attached_to_name. This panel, drag-and-drop, the REST endpoint and
// a row's own Attach control all go through it, and the app registers a File event
// server-side that files a record-level upload in the table. So the panel is left exactly as
// the framework built it: nothing here hides or replaces framework markup.
//
// A sealed correspondence refuses the file in File.before_insert, not here. The indicator
// below only says so before somebody picks a file and waits for an upload to fail.
// ---------------------------------------------------------------------------

// Pure: the rows the form should hold, given what it holds and what the server now has.
//
// Additive only. A row the user added or edited and has not saved yet carries no name from
// the server, so it is kept exactly as it is.
function murasalat_merge_attachment_rows(current, incoming) {
	const rows = (current || []).slice();
	const names = new Set(rows.map((row) => row.name).filter(Boolean));
	const files = new Set(rows.map((row) => row.file).filter(Boolean));

	(incoming || []).forEach((row) => {
		if ((row.name && names.has(row.name)) || (row.file && files.has(row.file))) {
			return;
		}

		// A row the server already holds must not look like a new one, or saving the form
		// would insert it a second time.
		const saved = Object.assign({}, row);
		delete saved.__islocal;

		rows.push(saved);
		names.add(saved.name);
		files.add(saved.file);
	});

	return rows;
}

// Bring the table in step with the server after an upload from the panel.
//
// This is not cosmetic. Frappe syncs a child table by deleting every row the submitted
// document does not contain, so a form that never learned about the row the File event
// created would erase it on the next save.
function murasalat_pull_attachment_rows(frm) {
	if (frm.is_new() || !frm.docname) {
		return;
	}

	frappe.db.get_doc(frm.doctype, frm.docname).then((doc) => {
		const merged = murasalat_merge_attachment_rows(frm.doc.attachments, doc.attachments);

		if (merged.length === (frm.doc.attachments || []).length) {
			return;
		}

		frm.doc.attachments = merged;
		frm.refresh_field("attachments");

		frappe.show_alert({
			message: __("أُضيف المرفق إلى الجدول."),
			indicator: "green",
		});
	});
}

// attachment_uploaded runs for every upload the panel completes. The upload widget is handed
// the panel's own completion callback and never reads one set on the control, so hooking that
// callback would never fire. This wraps the method instead, and delegates to it.
function murasalat_attachment_rules(frm) {
	if (frm.attachments && !frm.__murasalat_attach_hooked) {
		frm.__murasalat_attach_hooked = true;

		const native_attachment_uploaded = frm.attachments.attachment_uploaded;

		frm.attachments.attachment_uploaded = function (attachment) {
			const result = native_attachment_uploaded.call(this, attachment);

			murasalat_pull_attachment_rows(frm);

			return result;
		};
	}
}

frappe.ui.form.on("Murasalat Referral", {
	refresh(frm) {
		murasalat_attachment_rules(frm);
	},
});
