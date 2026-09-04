frappe.ui.form.on("Murasalat Correspondence", {
	setup(frm) {
		frm.set_query("correspondence_type", () => {
			const direction_field = {
				Internal: "allow_internal",
				Incoming: "allow_incoming",
				Outgoing: "allow_outgoing",
			}[frm.doc.direction];

			const filters = {
				is_active: 1,
			};

			if (direction_field) {
				filters[direction_field] = 1;
			}

			return { filters };
		});

		frm.set_query("confidentiality_level", () => ({
			filters: { is_active: 1 },
		}));

		frm.set_query("priority_level", () => ({
			filters: { is_active: 1 },
		}));

		frm.set_query("external_from_party", () => ({
			filters: { is_active: 1 },
		}));

		frm.set_query("external_to_party", () => ({
			filters: { is_active: 1 },
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
		apply_direction_from_route(frm);
		render_static_panels(frm);
		apply_direction_rules(frm);
	},

	refresh(frm) {
		apply_direction_rules(frm);
		configure_field_editability(frm);
		render_static_panels(frm);
		render_toolbar_buttons(frm);

		if (!frm.is_new()) {
			load_dashboard_data(frm);
		} else {
			render_empty_documents(frm);
			render_empty_referrals(frm);
		}
	},

	direction(frm) {
		apply_direction_rules(frm);
		frm.set_value("correspondence_type", null);
	},

	correspondence_type(frm) {
		apply_type_requirements(frm);
	},

	due_date(frm) {
		if (!frm.doc.due_date) {
			frm.set_value("due_date_hijri", null);
		}
	},

	external_letter_date(frm) {
		if (!frm.doc.external_letter_date) {
			frm.set_value("external_letter_date_hijri", null);
		}
	},

	outgoing_letter_date(frm) {
		if (!frm.doc.outgoing_letter_date) {
			frm.set_value("outgoing_letter_date_hijri", null);
		}
	},

	link_to_other_correspondence(frm) {
		frm.toggle_display(
			"correspondence_links",
			Boolean(frm.doc.link_to_other_correspondence)
		);

		if (
			!frm.doc.link_to_other_correspondence &&
			(frm.doc.correspondence_links || []).length
		) {
			frappe.confirm(
				__(
					"Disabling this option will remove all correspondence links. Continue?"
				),
				() => {
					frappe.model.clear_table(
						frm.doc,
						"correspondence_links"
					);
					frm.refresh_field("correspondence_links");
				},
				() => {
					frm.set_value(
						"link_to_other_correspondence",
						1
					);
				}
			);
		}
	},

	validate(frm) {
		validate_client_side(frm);
	},
});

frappe.ui.form.on("Murasalat Correspondence Link", {
	correspondence_links_add(frm) {
		const rows = frm.doc.correspondence_links || [];

		if (
			rows.length === 1 &&
			!rows.some((row) => row.is_primary_reference)
		) {
			frappe.model.set_value(
				rows[0].doctype,
				rows[0].name,
				"is_primary_reference",
				1
			);
		}
	},

	is_primary_reference(frm, cdt, cdn) {
		const selected = locals[cdt][cdn];

		if (!selected.is_primary_reference) {
			return;
		}

		(frm.doc.correspondence_links || []).forEach((row) => {
			if (row.name !== selected.name && row.is_primary_reference) {
				frappe.model.set_value(
					row.doctype,
					row.name,
					"is_primary_reference",
					0
				);
			}
		});
	},
});


function apply_direction_from_route(frm) {
	if (!frm.is_new()) {
		return;
	}

	const route_options = frappe.route_options || {};

	if (route_options.direction) {
		frm.set_value("direction", route_options.direction);
		frm.set_df_property("direction", "read_only", 1);
		return;
	}

	const route = frappe.get_route();
	const route_text = route.join("/").toLowerCase();

	if (route_text.includes("incoming")) {
		frm.set_value("direction", "Incoming");
		frm.set_df_property("direction", "read_only", 1);
	} else if (route_text.includes("outgoing")) {
		frm.set_value("direction", "Outgoing");
		frm.set_df_property("direction", "read_only", 1);
	} else if (route_text.includes("internal")) {
		frm.set_value("direction", "Internal");
		frm.set_df_property("direction", "read_only", 1);
	}
}


function apply_direction_rules(frm) {
	const direction = frm.doc.direction;

	const internal_fields = [
		"origin_department",
		"prepared_by",
		"prepared_by_employee",
	];

	const incoming_fields = [
		"external_from_party",
		"incoming_to_department",
		"external_letter_number",
		"external_letter_date",
		"external_letter_date_hijri",
	];

	const outgoing_fields = [
		"outgoing_from_department",
		"external_to_party",
		"outgoing_letter_number",
		"outgoing_letter_date",
		"outgoing_letter_date_hijri",
	];

	frm.toggle_display(internal_fields, direction === "Internal");
	frm.toggle_display(incoming_fields, direction === "Incoming");
	frm.toggle_display(outgoing_fields, direction === "Outgoing");

	frm.toggle_reqd("origin_department", direction === "Internal");

	frm.toggle_reqd("external_from_party", direction === "Incoming");
	frm.toggle_reqd("incoming_to_department", direction === "Incoming");

	frm.toggle_reqd(
		"outgoing_from_department",
		direction === "Outgoing"
	);
	frm.toggle_reqd("external_to_party", direction === "Outgoing");

	apply_type_requirements(frm);
}


async function apply_type_requirements(frm) {
	if (!frm.doc.correspondence_type) {
		frm.toggle_reqd("external_letter_number", false);
		frm.toggle_reqd("external_letter_date", false);
		frm.toggle_reqd("outgoing_letter_number", false);
		frm.toggle_reqd("outgoing_letter_date", false);
		return;
	}

	const result = await frappe.db.get_value(
		"Murasalat Correspondence Type",
		frm.doc.correspondence_type,
		[
			"requires_letter_number",
			"requires_letter_date",
		]
	);

	const values = result.message || {};
	const requires_number = Boolean(values.requires_letter_number);
	const requires_date = Boolean(values.requires_letter_date);

	frm.toggle_reqd(
		"external_letter_number",
		frm.doc.direction === "Incoming" && requires_number
	);

	frm.toggle_reqd(
		"external_letter_date",
		frm.doc.direction === "Incoming" && requires_date
	);

	frm.toggle_reqd(
		"outgoing_letter_number",
		frm.doc.direction === "Outgoing" && requires_number
	);

	frm.toggle_reqd(
		"outgoing_letter_date",
		frm.doc.direction === "Outgoing" && requires_date
	);
}


function configure_field_editability(frm) {
	const immutable_fields = [
		"direction",
		"correspondence_type",
		"company",
		"owner_department",
		"subject",
		"confidentiality_level",
		"priority_level",
		"origin_department",
		"external_from_party",
		"incoming_to_department",
		"external_letter_number",
		"external_letter_date",
		"outgoing_from_department",
		"external_to_party",
		"outgoing_letter_number",
		"outgoing_letter_date",
	];

	if (frm.doc.docstatus === 1) {
		frm.toggle_enable(immutable_fields, false);
	} else {
		frm.toggle_enable(immutable_fields, true);
	}
}


function render_toolbar_buttons(frm) {
	frm.clear_custom_buttons();

	if (frm.is_new()) {
		frm.add_custom_button(
			__("Clear Fields"),
			() => clear_new_form(frm),
			__("Actions")
		);

		frm.add_custom_button(
			__("Save as Draft"),
			() => frm.save(),
			__("Actions")
		);

		return;
	}

	frm.add_custom_button(
		__("Refresh Panels"),
		() => load_dashboard_data(frm),
		__("Actions")
	);

	frm.add_custom_button(
		__("Print Barcode"),
		() => open_print_view(frm),
		__("Actions")
	);

	frm.add_custom_button(
		__("Add Document"),
		() => create_document(frm, "Upload"),
		__("Documents")
	);

	frm.add_custom_button(
		__("Add Scanned Document"),
		() => create_document(frm, "Scanner"),
		__("Documents")
	);

	if (frm.doc.docstatus === 1 && frm.doc.workflow_state !== "Murasalat Closed") {
		frm.add_custom_button(
			__("Single Referral"),
			() => create_single_referral(frm),
			__("Referrals")
		);

		frm.add_custom_button(
			__("Multiple Referral"),
			() => open_multiple_referral_dialog(frm),
			__("Referrals")
		);
	}
}


function render_static_panels(frm) {
	render_data_actions(frm);
	render_attachment_intro(frm);
	render_attachment_actions(frm);
	render_referral_intro(frm);
	render_referral_actions(frm);
}


function render_data_actions(frm) {
	const wrapper = frm.fields_dict.data_actions_html?.$wrapper;

	if (!wrapper) {
		return;
	}

	wrapper.html(`
		<div class="murasalat-action-bar"
			style="display:flex;gap:8px;justify-content:flex-end;padding:12px 0;">
			<button type="button"
				class="btn btn-default btn-sm"
				data-action="clear">
				${__("Clear Fields")}
			</button>
			<button type="button"
				class="btn btn-default btn-sm"
				data-action="save-draft">
				${__("Save as Draft")}
			</button>
			<button type="button"
				class="btn btn-primary btn-sm"
				data-action="next-attachments">
				${__("Next")}
			</button>
		</div>
	`);

	wrapper
		.off(".murasalat")
		.on("click.murasalat", '[data-action="clear"]', () => {
			clear_new_form(frm);
		})
		.on("click.murasalat", '[data-action="save-draft"]', () => {
			frm.save();
		})
		.on(
			"click.murasalat",
			'[data-action="next-attachments"]',
			() => {
				activate_tab(frm, "attachments_tab");
			}
		);
}


function render_attachment_intro(frm) {
	const wrapper = frm.fields_dict.attachments_intro_html?.$wrapper;

	if (!wrapper) {
		return;
	}

	wrapper.html(`
		<div class="alert alert-info">
			${__(
				"Save the correspondence first, then add the main letter, attachments, or reply documents."
			)}
		</div>
	`);
}


function render_attachment_actions(frm) {
	const wrapper = frm.fields_dict.attachments_actions_html?.$wrapper;

	if (!wrapper) {
		return;
	}

	wrapper.html(`
		<div class="murasalat-action-bar"
			style="display:flex;gap:8px;justify-content:space-between;padding:12px 0;">
			<div>
				<button type="button"
					class="btn btn-default btn-sm"
					data-action="previous-data">
					${__("Previous")}
				</button>
			</div>
			<div style="display:flex;gap:8px;">
				<button type="button"
					class="btn btn-default btn-sm"
					data-action="add-document">
					${__("Attach from Device")}
				</button>
				<button type="button"
					class="btn btn-default btn-sm"
					data-action="add-scanned-document">
					${__("Scan")}
				</button>
				<button type="button"
					class="btn btn-primary btn-sm"
					data-action="next-referrals">
					${__("Next")}
				</button>
			</div>
		</div>
	`);

	wrapper
		.off(".murasalat")
		.on("click.murasalat", '[data-action="previous-data"]', () => {
			activate_tab(frm, "data_tab");
		})
		.on("click.murasalat", '[data-action="add-document"]', () => {
			create_document(frm, "Upload");
		})
		.on(
			"click.murasalat",
			'[data-action="add-scanned-document"]',
			() => {
				create_document(frm, "Scanner");
			}
		)
		.on("click.murasalat", '[data-action="next-referrals"]', () => {
			activate_tab(frm, "referrals_tab");
		});
}


function render_referral_intro(frm) {
	const wrapper = frm.fields_dict.referrals_intro_html?.$wrapper;

	if (!wrapper) {
		return;
	}

	const message =
		frm.doc.docstatus === 1
			? __(
					"Create one or more independent referrals. Every recipient will receive a separate referral record."
			  )
			: __(
					"Register the correspondence before sending referrals."
			  );

	const indicator =
		frm.doc.docstatus === 1 ? "alert-info" : "alert-warning";

	wrapper.html(`
		<div class="alert ${indicator}">
			${message}
		</div>
	`);
}


function render_referral_actions(frm) {
	const wrapper = frm.fields_dict.referrals_actions_html?.$wrapper;

	if (!wrapper) {
		return;
	}

	const disabled = frm.doc.docstatus !== 1 ? "disabled" : "";

	wrapper.html(`
		<div class="murasalat-action-bar"
			style="display:flex;gap:8px;justify-content:space-between;padding:12px 0;">
			<button type="button"
				class="btn btn-default btn-sm"
				data-action="previous-attachments">
				${__("Previous")}
			</button>
			<div style="display:flex;gap:8px;">
				<button type="button"
					class="btn btn-default btn-sm"
					data-action="single-referral"
					${disabled}>
					${__("Single Referral")}
				</button>
				<button type="button"
					class="btn btn-primary btn-sm"
					data-action="multiple-referral"
					${disabled}>
					${__("Multiple Referral")}
				</button>
			</div>
		</div>
	`);

	wrapper
		.off(".murasalat")
		.on(
			"click.murasalat",
			'[data-action="previous-attachments"]',
			() => {
				activate_tab(frm, "attachments_tab");
			}
		)
		.on("click.murasalat", '[data-action="single-referral"]', () => {
			create_single_referral(frm);
		})
		.on(
			"click.murasalat",
			'[data-action="multiple-referral"]',
			() => {
				open_multiple_referral_dialog(frm);
			}
		);
}


function activate_tab(frm, tabFieldname) {
	const targetTab = (frm.layout.tabs || []).find(
		(tab) => tab.df.fieldname === tabFieldname
	);

	if (targetTab && typeof targetTab.set_active === "function") {
		targetTab.set_active();
		window.scrollTo({
			top: frm.wrapper.offsetTop || 0,
			behavior: "smooth",
		});
		return;
	}

	const tabButton = frm.wrapper.querySelector(
		`.nav-link[data-fieldname="${tabFieldname}"]`
	);

	if (tabButton) {
		tabButton.click();
	}
}


function clear_new_form(frm) {
	if (!frm.is_new()) {
		frappe.msgprint(
			__("Only a new unsaved correspondence can be cleared.")
		);
		return;
	}

	frappe.confirm(
		__("Clear all entered correspondence data?"),
		() => {
			const preservedDirection = frm.doc.direction;

			frappe.model.clear_doc(frm.doctype, frm.doc.name);

			frappe.new_doc(
				"Murasalat Correspondence",
				preservedDirection
					? { direction: preservedDirection }
					: {}
			);
		}
	);
}


function create_document(frm, sourceType) {
	if (frm.is_new()) {
		frappe.msgprint(
			__("Save the correspondence before adding documents.")
		);
		return;
	}

	frappe.new_doc(
		"Murasalat Correspondence Document",
		{
			correspondence: frm.doc.name,
			source_type: sourceType,
		}
	);
}


function create_single_referral(frm) {
	if (!ensure_referral_allowed(frm)) {
		return;
	}

	frappe.new_doc(
		"Murasalat Referral",
		{
			correspondence: frm.doc.name,
			priority_level: frm.doc.priority_level,
		}
	);
}


function ensure_referral_allowed(frm) {
	if (frm.is_new()) {
		frappe.msgprint(
			__("Save and register the correspondence first.")
		);
		return false;
	}

	if (frm.doc.docstatus !== 1) {
		frappe.msgprint(
			__("The correspondence must be registered before referral.")
		);
		return false;
	}

	if (frm.doc.workflow_state === "Murasalat Closed") {
		frappe.msgprint(
			__("Closed correspondence cannot be referred.")
		);
		return false;
	}

	return true;
}


function open_multiple_referral_dialog(frm) {
	if (!ensure_referral_allowed(frm)) {
		return;
	}

	const dialog = new frappe.ui.Dialog({
		title: __("Multiple Referral"),
		size: "extra-large",
		fields: [
			{
				fieldname: "referrals",
				fieldtype: "Table",
				label: __("Referral Recipients"),
				cannot_add_rows: false,
				in_place_edit: true,
				reqd: 1,
				data: [],
				fields: [
					{
						fieldname: "recipient_type",
						fieldtype: "Select",
						label: __("Recipient Type"),
						options: "Department\nUser",
						default: "Department",
						in_list_view: 1,
						reqd: 1,
					},
					{
						fieldname: "to_department",
						fieldtype: "Link",
						label: __("To Department"),
						options: "Department",
						in_list_view: 1,
					},
					{
						fieldname: "to_user",
						fieldtype: "Link",
						label: __("To User"),
						options: "User",
						in_list_view: 1,
					},
					{
						fieldname: "routing_purpose",
						fieldtype: "Link",
						label: __("Routing Purpose"),
						options: "Murasalat Routing Purpose",
						in_list_view: 1,
						reqd: 1,
					},
					{
						fieldname: "priority_level",
						fieldtype: "Link",
						label: __("Priority Level"),
						options: "Murasalat Priority Level",
						default: frm.doc.priority_level,
						in_list_view: 1,
						reqd: 1,
					},
					{
						fieldname: "due_date",
						fieldtype: "Date",
						label: __("Due Date"),
						in_list_view: 1,
					},
					{
						fieldname: "instructions",
						fieldtype: "Small Text",
						label: __("Instructions"),
						in_list_view: 1,
					},
					{
						fieldname: "is_private",
						fieldtype: "Check",
						label: __("Private"),
						in_list_view: 1,
					},
					{
						fieldname: "paper_correspondence",
						fieldtype: "Check",
						label: __("Paper Correspondence"),
						in_list_view: 1,
					},
					{
						fieldname: "send_copy",
						fieldtype: "Check",
						label: __("Send Copy"),
						in_list_view: 1,
					},
					{
						fieldname: "for_follow_up",
						fieldtype: "Check",
						label: __("For Follow Up"),
						in_list_view: 1,
					},
				],
			},
		],
		primary_action_label: __("Send"),
		primary_action(values) {
			const rows = values.referrals || [];

			if (!rows.length) {
				frappe.msgprint(
					__("Add at least one referral recipient.")
				);
				return;
			}

			validate_dialog_referrals(rows);

			dialog.get_primary_btn().prop("disabled", true);

			frm.call("create_multiple_referrals", {
				referrals: rows,
			})
				.then((response) => {
					const result = response.message || {};

					dialog.hide();

					frappe.show_alert(
						{
							message: __(
								"{0} referrals were created successfully.",
								[result.created_count || 0]
							),
							indicator: "green",
						},
						7
					);

					return frm.reload_doc();
				})
				.then(() => load_dashboard_data(frm))
				.finally(() => {
					dialog.get_primary_btn().prop("disabled", false);
				});
		},
	});

	dialog.show();
}


function validate_dialog_referrals(rows) {
	const seen = new Set();

	rows.forEach((row, index) => {
		const rowNumber = index + 1;

		if (!row.recipient_type) {
			frappe.throw(
				__("Recipient Type is required in row {0}.", [
					rowNumber,
				])
			);
		}

		if (
			row.recipient_type === "Department" &&
			!row.to_department
		) {
			frappe.throw(
				__("To Department is required in row {0}.", [
					rowNumber,
				])
			);
		}

		if (row.recipient_type === "User" && !row.to_user) {
			frappe.throw(
				__("To User is required in row {0}.", [
					rowNumber,
				])
			);
		}

		if (!row.routing_purpose) {
			frappe.throw(
				__("Routing Purpose is required in row {0}.", [
					rowNumber,
				])
			);
		}

		const recipient =
			row.recipient_type === "User"
				? row.to_user
				: row.to_department;

		const key = `${row.recipient_type}:${recipient}`;

		if (seen.has(key)) {
			frappe.throw(
				__("Duplicate recipient in row {0}: {1}", [
					rowNumber,
					recipient,
				])
			);
		}

		seen.add(key);
	});
}


function load_dashboard_data(frm) {
	if (frm.is_new()) {
		return;
	}

	frm.call("get_form_dashboard_data").then((response) => {
		const data = response.message || {
			documents: [],
			referrals: [],
		};

		render_documents(frm, data.documents || []);
		render_referrals(frm, data.referrals || []);
	});
}


function render_empty_documents(frm) {
	const wrapper = frm.fields_dict.documents_html?.$wrapper;

	if (wrapper) {
		wrapper.html(`
			<div class="text-muted" style="padding:16px;">
				${__("Save the correspondence to view documents.")}
			</div>
		`);
	}
}


function render_documents(frm, documents) {
	const wrapper = frm.fields_dict.documents_html?.$wrapper;

	if (!wrapper) {
		return;
	}

	if (!documents.length) {
		wrapper.html(`
			<div class="text-muted" style="padding:16px;">
				${__("No documents have been added.")}
			</div>
		`);
		return;
	}

	const rows = documents
		.map((document) => {
			const name = escapeHtml(document.name);
			const fileName = escapeHtml(
				document.file_name || document.file || ""
			);
			const category = escapeHtml(
				document.document_category || ""
			);
			const type = escapeHtml(document.document_type || "");
			const badges = [
				document.is_main_document
					? `<span class="indicator-pill green">${__(
							"Main Letter"
					  )}</span>`
					: "",
				document.is_secret
					? `<span class="indicator-pill red">${__(
							"Secret"
					  )}</span>`
					: "",
			].join(" ");

			return `
				<tr>
					<td>
						<a href="#" data-document="${name}">
							${fileName || name}
						</a>
					</td>
					<td>${category}</td>
					<td>${type}</td>
					<td>${badges}</td>
					<td>${escapeHtml(document.uploaded_by || "")}</td>
					<td>${escapeHtml(document.uploaded_on || "")}</td>
				</tr>
			`;
		})
		.join("");

	wrapper.html(`
		<div class="table-responsive">
			<table class="table table-bordered table-hover">
				<thead>
					<tr>
						<th>${__("File")}</th>
						<th>${__("Document Category")}</th>
						<th>${__("Document Type")}</th>
						<th>${__("Classification")}</th>
						<th>${__("Uploaded By")}</th>
						<th>${__("Uploaded On")}</th>
					</tr>
				</thead>
				<tbody>${rows}</tbody>
			</table>
		</div>
	`);

	wrapper
		.off(".murasalat")
		.on("click.murasalat", "[data-document]", function (event) {
			event.preventDefault();
			frappe.set_route(
				"Form",
				"Murasalat Correspondence Document",
				this.dataset.document
			);
		});
}


function render_empty_referrals(frm) {
	const wrapper = frm.fields_dict.referrals_html?.$wrapper;

	if (wrapper) {
		wrapper.html(`
			<div class="text-muted" style="padding:16px;">
				${__("Save and register the correspondence to view referrals.")}
			</div>
		`);
	}
}


function render_referrals(frm, referrals) {
	const wrapper = frm.fields_dict.referrals_html?.$wrapper;

	if (!wrapper) {
		return;
	}

	if (!referrals.length) {
		wrapper.html(`
			<div class="text-muted" style="padding:16px;">
				${__("No referrals have been created.")}
			</div>
		`);
		return;
	}

	const rows = referrals
		.map((referral) => {
			const name = escapeHtml(referral.name);
			const recipient =
				referral.recipient_type === "User"
					? referral.to_user
					: referral.to_department;

			const copyBadge = referral.is_copy
				? `<span class="indicator-pill blue">${__(
						"Copy"
				  )}</span>`
				: "";

			return `
				<tr>
					<td>
						<a href="#" data-referral="${name}">
							${name}
						</a>
					</td>
					<td>${escapeHtml(recipient || "")}</td>
					<td>${escapeHtml(referral.routing_purpose || "")}</td>
					<td>${escapeHtml(referral.priority_level || "")}</td>
					<td>${escapeHtml(referral.due_date || "")}</td>
					<td>${escapeHtml(referral.status || "")} ${copyBadge}</td>
					<td>${escapeHtml(referral.sent_on || "")}</td>
				</tr>
			`;
		})
		.join("");

	wrapper.html(`
		<div class="table-responsive">
			<table class="table table-bordered table-hover">
				<thead>
					<tr>
						<th>${__("Referral")}</th>
						<th>${__("To")}</th>
						<th>${__("Routing Purpose")}</th>
						<th>${__("Priority Level")}</th>
						<th>${__("Due Date")}</th>
						<th>${__("Status")}</th>
						<th>${__("Sent On")}</th>
					</tr>
				</thead>
				<tbody>${rows}</tbody>
			</table>
		</div>
	`);

	wrapper
		.off(".murasalat")
		.on("click.murasalat", "[data-referral]", function (event) {
			event.preventDefault();
			frappe.set_route(
				"Form",
				"Murasalat Referral",
				this.dataset.referral
			);
		});
}


function open_print_view(frm) {
	if (frm.is_new()) {
		frappe.msgprint(
			__("Save the correspondence before printing.")
		);
		return;
	}

	frappe.set_route(
		"print",
		frm.doctype,
		frm.doc.name
	);
}


function validate_client_side(frm) {
	if (!frm.doc.subject) {
		frappe.throw(__("Subject is required."));
	}

	if (frm.doc.direction === "Incoming") {
		if (!frm.doc.external_from_party) {
			frappe.throw(__("External Sender is required."));
		}

		if (!frm.doc.incoming_to_department) {
			frappe.throw(
				__("Internal Recipient Department is required.")
			);
		}
	}

	if (frm.doc.direction === "Outgoing") {
		if (!frm.doc.outgoing_from_department) {
			frappe.throw(__("Sending Department is required."));
		}

		if (!frm.doc.external_to_party) {
			frappe.throw(__("External Recipient is required."));
		}
	}
}


function escapeHtml(value) {
	return $("<div>").text(value || "").html();
}