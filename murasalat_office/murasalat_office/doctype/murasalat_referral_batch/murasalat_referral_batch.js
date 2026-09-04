frappe.ui.form.on("Murasalat Referral Batch", {
	setup(frm) {
		frm.set_query("correspondence", () => ({
			filters: {
				docstatus: 1,
				workflow_state: [
					"!=",
					"Murasalat Closed",
				],
			},
		}));

		frm.set_query("default_routing_purpose", () => ({
			filters: {
				is_active: 1,
			},
		}));

		frm.set_query("default_priority_level", () => ({
			filters: {
				is_active: 1,
			},
		}));

		frm.set_query(
			"routing_purpose",
			"recipients",
			() => ({
				filters: {
					is_active: 1,
				},
			})
		);

		frm.set_query(
			"priority_level",
			"recipients",
			() => ({
				filters: {
					is_active: 1,
				},
			})
		);

		frm.set_query(
			"to_user",
			"recipients",
			() => ({
				filters: {
					enabled: 1,
					user_type: "System User",
				},
			})
		);
	},

	default_routing_purpose(frm) {
		apply_default_to_empty_rows(
			frm,
			"routing_purpose",
			frm.doc.default_routing_purpose
		);
	},

	default_priority_level(frm) {
		apply_default_to_empty_rows(
			frm,
			"priority_level",
			frm.doc.default_priority_level
		);
	},

	default_due_date(frm) {
		apply_default_to_empty_rows(
			frm,
			"due_date",
			frm.doc.default_due_date
		);
	},
});


frappe.ui.form.on("Murasalat Referral Batch Item", {
	recipients_add(frm, cdt, cdn) {
		const row = frappe.get_doc(cdt, cdn);

		frappe.model.set_value(
			cdt,
			cdn,
			"routing_purpose",
			row.routing_purpose
				|| frm.doc.default_routing_purpose
		);

		frappe.model.set_value(
			cdt,
			cdn,
			"priority_level",
			row.priority_level
				|| frm.doc.default_priority_level
		);

		frappe.model.set_value(
			cdt,
			cdn,
			"due_date",
			row.due_date
				|| frm.doc.default_due_date
		);
	},

	recipient_type(frm, cdt, cdn) {
		const row = frappe.get_doc(cdt, cdn);

		if (row.recipient_type === "User") {
			frappe.model.set_value(
				cdt,
				cdn,
				"to_department",
				null
			);
		}

		if (row.recipient_type === "Department") {
			frappe.model.set_value(
				cdt,
				cdn,
				"to_user",
				null
			);
		}
	},
});


function apply_default_to_empty_rows(
	frm,
	fieldname,
	value
) {
	if (!value) {
		return;
	}

	(frm.doc.recipients || []).forEach((row) => {
		if (!row[fieldname]) {
			frappe.model.set_value(
				row.doctype,
				row.name,
				fieldname,
				value
			);
		}
	});
}