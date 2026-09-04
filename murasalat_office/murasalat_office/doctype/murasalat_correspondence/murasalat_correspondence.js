frappe.ui.form.on("Murasalat Correspondence", {
	setup(frm) {
		frm.set_query("correspondence_type", () => {
			const filters = {
				is_active: 1,
			};

			if (frm.doc.direction) {
				filters.direction = frm.doc.direction;
			}

			return { filters };
		});

		frm.set_query("confidentiality_level", () => ({
			filters: {
				is_active: 1,
			},
		}));

		frm.set_query("priority_level", () => ({
			filters: {
				is_active: 1,
			},
		}));

		frm.set_query("external_from_party", () => ({
			filters: {
				is_active: 1,
			},
		}));

		frm.set_query("external_to_party", () => ({
			filters: {
				is_active: 1,
			},
		}));

		frm.set_query(
			"linked_correspondence",
			"correspondence_links",
			() => ({
				filters: {
					name: ["!=", frm.doc.name || ""],
					docstatus: ["!=", 2],
				},
			})
		);
	},

	onload(frm) {
		apply_route_defaults(frm);
	},

	refresh(frm) {
		add_create_buttons(frm);
		show_contextual_message(frm);
	},

	direction(frm) {
		if (frm.doc.correspondence_type) {
			frm.set_value("correspondence_type", null);
		}
	},
});


function apply_route_defaults(frm) {
	if (!frm.is_new() || !frappe.route_options) {
		return;
	}

	const allowed_fields = [
		"direction",
		"correspondence_type",
		"company",
		"owner_department",
		"priority_level",
		"confidentiality_level",
	];

	const values = {};

	allowed_fields.forEach((fieldname) => {
		if (frappe.route_options[fieldname] !== undefined) {
			values[fieldname] = frappe.route_options[fieldname];
		}
	});

	if (Object.keys(values).length) {
		frm.set_value(values);
	}
}


function add_create_buttons(frm) {
	if (frm.is_new()) {
		return;
	}

	frm.add_custom_button(
		__("Add Document"),
		() => create_document(frm),
		__("Create")
	);

	if (
		frm.doc.docstatus === 1 &&
		frm.doc.workflow_state !== "Murasalat Closed"
	) {
		frm.add_custom_button(
			__("Single Referral"),
			() => create_single_referral(frm),
			__("Create")
		);

		frm.add_custom_button(
			__("Multiple Referral"),
			() => create_referral_batch(frm),
			__("Create")
		);
	}
}


function create_document(frm) {
	frappe.new_doc(
		"Murasalat Correspondence Document",
		{
			correspondence: frm.doc.name,
			source_type: "Upload",
		}
	);
}


function create_single_referral(frm) {
	if (frm.doc.docstatus !== 1) {
		frappe.msgprint({
			title: __("Registration Required"),
			message: __(
				"Register the correspondence before sending referrals."
			),
			indicator: "orange",
		});
		return;
	}

	frappe.new_doc(
		"Murasalat Referral",
		{
			correspondence: frm.doc.name,
			from_user: frappe.session.user,
			from_department: frm.doc.owner_department,
			priority_level: frm.doc.priority_level,
		}
	);
}


function create_referral_batch(frm) {
	if (frm.doc.docstatus !== 1) {
		frappe.msgprint({
			title: __("Registration Required"),
			message: __(
				"Register the correspondence before sending referrals."
			),
			indicator: "orange",
		});
		return;
	}

	frappe.new_doc(
		"Murasalat Referral Batch",
		{
			correspondence: frm.doc.name,
			from_user: frappe.session.user,
			from_department: frm.doc.owner_department,
			default_priority_level: frm.doc.priority_level,
		}
	);
}


function show_contextual_message(frm) {
	if (frm.is_new()) {
		frm.set_intro(
			__(
				"Save the correspondence first, then add the main letter, attachments, or reply documents."
			),
			"blue"
		);
		return;
	}

	if (frm.doc.docstatus === 0) {
		frm.set_intro(
			__(
				"Register the correspondence before sending referrals."
			),
			"orange"
		);
		return;
	}

	if (frm.doc.workflow_state === "Murasalat Closed") {
		frm.set_intro(
			__("This correspondence is closed."),
			"green"
		);
	}
}