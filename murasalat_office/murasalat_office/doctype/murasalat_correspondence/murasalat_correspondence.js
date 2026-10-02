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

        // The button is rendered only after a server-side eligibility/permission check.
        // The server remains authoritative; the button is UX, not security.
        frappe.call({
            method: "murasalat_office.api.operations.get_reply_context",
            args: { correspondence: frm.doc.name },
            callback(r) {
                if (r && r.message && r.message.can_create_reply) {
                    frm.add_custom_button(
                        __("Create Reply"),
                        () => murasalat_create_reply(frm),
                        __("Create"),
                    );
                }
            },
        });
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
	if (frm.doc.record_sealed_on && !frm.__murasalat_seal_notice) {
		frm.__murasalat_seal_notice = true;
		frm.dashboard.add_indicator(__("مختومة - المرفقات مقفلة"), "green");
	}

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

frappe.ui.form.on("Murasalat Correspondence", {
	refresh(frm) {
		murasalat_attachment_rules(frm);
	},
});

function murasalat_create_reply(frm) {
	frappe.call({
		method: "murasalat_office.api.operations.get_reply_context",
		args: { correspondence: frm.doc.name },
	}).then((r) => {
		const context = r && r.message;
		if (!context) {
			frappe.msgprint({ title: __("Create Official Reply"), message: __("Unable to load the reply context."), indicator: "red" });
			return;
		}
		if (!context.can_create_reply) {
			frappe.msgprint({
				title: __("Reply cannot be created"),
				message: (context.blockers || []).join("<br>"),
				indicator: "orange",
			});
			return;
		}

		const dialog = new frappe.ui.Dialog({
			title: __("Reply by Letter"),
			size: "extra-large",
			fields: [
				{ fieldtype: "Section Break", label: __("Reply Reference") },
				{ fieldname: "source_correspondence", fieldtype: "Data", label: __("Reply To"), default: context.incoming.name, read_only: 1 },
				{ fieldname: "recipient", fieldtype: "Link", options: "Murasalat External Party", label: __("Recipient"), default: context.default_target_external_party, read_only: 1 },
				{ fieldname: "source_department", fieldtype: "Link", options: "Department", label: __("Preparation Department"), default: context.default_source_department, read_only: 1 },
				{ fieldname: "subject", fieldtype: "Data", label: __("Subject"), reqd: 1, default: __("Reply: {0}", [context.incoming.subject || ""]) },
				{ fieldname: "salutation", fieldtype: "Data", label: __("Salutation"), default: __("السادة/") },
				{ fieldtype: "Section Break", label: __("Letter Body") },
				{ fieldname: "notes", fieldtype: "Text Editor", label: __("Body"), reqd: 1 },
				{ fieldname: "closing_phrase", fieldtype: "Data", label: __("Closing Phrase"), default: __("وتفضلوا بقبول خالص التحية والتقدير") },
				{ fieldtype: "Section Break", label: __("Signature & Approval") },
				{ fieldname: "signatory_name", fieldtype: "Data", label: __("Signatory Name") },
				{ fieldname: "signatory_position", fieldtype: "Data", label: __("Signatory Position") },
				{ fieldname: "approval_entity", fieldtype: "Link", options: "Department", label: __("Approval Entity") },
				{ fieldname: "preparation_entity", fieldtype: "Link", options: "Department", label: __("Preparation Entity"), default: context.default_source_department },
				{ fieldname: "prepared_on", fieldtype: "Date", label: __("Preparation Date"), default: frappe.datetime.get_today() },
			],
		primary_action_label: __("Create Letter Draft"),
		primary_action(values) {
			if (!values.notes || !String(values.notes).trim()) {
				frappe.msgprint({ title: __("Letter Body Required"), message: __("Enter the official letter body before creating the draft."), indicator: "orange" });
				return;
			}
			frappe.call({
				method: "murasalat_office.api.operations.create_reply_draft",
				args: {
					correspondence: frm.doc.name,
					subject: values.subject,
					notes: values.notes,
					source_department: values.source_department,
					salutation: values.salutation,
					closing_phrase: values.closing_phrase,
					signatory_name: values.signatory_name,
					signatory_position: values.signatory_position,
					approval_entity: values.approval_entity,
					preparation_entity: values.preparation_entity,
					prepared_on: values.prepared_on,
				},
				freeze: true,
				freeze_message: __("Creating official reply draft…"),
			}).then((response) => {
				const result = response && response.message;
				if (!result || !result.name) return;
				dialog.hide();
				frappe.show_alert({ message: __("Official reply draft {0} created.", [result.name]), indicator: "green" });
				frappe.set_route("Form", "Murasalat Correspondence", result.name);
			});
		},
	});
	dialog.show();
	});
}
