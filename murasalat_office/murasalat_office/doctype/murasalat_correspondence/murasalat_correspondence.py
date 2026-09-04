from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.naming import make_autoname
from frappe.utils import cint, getdate, now, nowdate

from murasalat_office.utils.hijri import (
	current_hijri_year,
	gregorian_to_hijri,
)


CLOSED_WORKFLOW_STATE = "Murasalat Closed"

FINAL_REFERRAL_STATUSES = {
	"Completed",
	"Withdrawn",
	"Cancelled",
}

DIRECTION_FIELDS = {
	"Internal": (
		"origin_department",
		"prepared_by",
		"prepared_by_employee",
	),
	"Incoming": (
		"external_from_party",
		"incoming_to_department",
		"external_letter_number",
		"external_letter_date",
		"external_letter_date_hijri",
	),
	"Outgoing": (
		"outgoing_from_department",
		"external_to_party",
		"outgoing_letter_number",
		"outgoing_letter_date",
		"outgoing_letter_date_hijri",
	),
}


class MurasalatCorrespondence(Document):
	def before_validate(self):
		self.set_defaults()
		self.clear_irrelevant_direction_fields()
		self.set_hijri_dates()
		self.set_identification_values()

	def before_insert(self):
		if not self.correspondence_number:
			self.correspondence_number = (
				self.generate_correspondence_number()
			)

		self.set_identification_values()

	def validate(self):
		self.validate_direction()
		self.validate_correspondence_type()
		self.validate_due_date()
		self.validate_correspondence_links()

	def before_submit(self):
		self.validate_required_main_document()
		self.validate_closed_state()

		if not self.registered_by:
			self.registered_by = frappe.session.user

		if not self.registered_on:
			self.registered_on = now()

		self.set_identification_values()

	def before_update_after_submit(self):
		self.validate_closed_state()
		self.set_closed_information()

	def before_cancel(self):
		self.validate_no_active_referrals(
			_("Cancel")
		)

	def on_trash(self):
		self.validate_no_linked_transactions()

	def set_defaults(self):
		if not self.company:
			self.company = (
				frappe.defaults.get_user_default("Company")
				or self.get_settings_value("default_company")
			)

		if not self.owner_department:
			self.owner_department = (
				frappe.defaults.get_user_default("Department")
				or self.get_settings_value("default_department")
			)

		if not self.confidentiality_level:
			self.confidentiality_level = (
				self.get_settings_value(
					"default_confidentiality"
				)
			)

		if not self.priority_level:
			self.priority_level = self.get_settings_value(
				"default_priority"
			)

		if (
			self.direction == "Internal"
			and not self.prepared_by
		):
			self.prepared_by = frappe.session.user

		if (
			self.direction == "Internal"
			and not self.origin_department
		):
			self.origin_department = self.owner_department

		if (
			self.direction == "Outgoing"
			and not self.outgoing_from_department
		):
			self.outgoing_from_department = (
				self.owner_department
			)

		if (
			self.direction == "Incoming"
			and not self.incoming_to_department
		):
			self.incoming_to_department = (
				self.owner_department
			)

	def get_settings_value(self, fieldname):
		if not frappe.db.exists(
			"DocType",
			"Murasalat Settings",
		):
			return None

		meta = frappe.get_meta("Murasalat Settings")

		if not meta.issingle or not meta.has_field(fieldname):
			return None

		return frappe.db.get_single_value(
			"Murasalat Settings",
			fieldname,
		)

	def clear_irrelevant_direction_fields(self):
		selected_fields = set(
			DIRECTION_FIELDS.get(self.direction, ())
		)

		for fields in DIRECTION_FIELDS.values():
			for fieldname in fields:
				if fieldname not in selected_fields:
					self.set(fieldname, None)

	def set_hijri_dates(self):
		self.due_date_hijri = gregorian_to_hijri(
			self.due_date
		)

		self.external_letter_date_hijri = (
			gregorian_to_hijri(
				self.external_letter_date
			)
		)

		self.outgoing_letter_date_hijri = (
			gregorian_to_hijri(
				self.outgoing_letter_date
			)
		)

	def set_identification_values(self):
		if not self.correspondence_number:
			return

		self.barcode = self.correspondence_number
		self.qr_code = self.correspondence_number

	def validate_direction(self):
		if self.direction not in DIRECTION_FIELDS:
			frappe.throw(
				_("Please select a valid correspondence direction.")
			)

		if self.direction == "Internal":
			if not self.origin_department:
				frappe.throw(
					_("Origin Department is required.")
				)

		elif self.direction == "Incoming":
			if not self.external_from_party:
				frappe.throw(
					_("External Sender is required.")
				)

			if not self.incoming_to_department:
				frappe.throw(
					_(
						"Internal Recipient Department "
						"is required."
					)
				)

		elif self.direction == "Outgoing":
			if not self.outgoing_from_department:
				frappe.throw(
					_("Sending Department is required.")
				)

			if not self.external_to_party:
				frappe.throw(
					_("External Recipient is required.")
				)

	def validate_correspondence_type(self):
		if not self.correspondence_type:
			return

		type_doc = frappe.get_cached_doc(
			"Murasalat Correspondence Type",
			self.correspondence_type,
		)

		if type_doc.meta.has_field("is_active"):
			if not cint(type_doc.is_active):
				frappe.throw(
					_(
						"Correspondence Type {0} is inactive."
					).format(
						frappe.bold(
							self.correspondence_type
						)
					)
				)

		type_direction = type_doc.get("direction")

		if (
			type_direction
			and type_direction != self.direction
		):
			frappe.throw(
				_(
					"Correspondence Type {0} is configured "
					"for direction {1}, not {2}."
				).format(
					frappe.bold(self.correspondence_type),
					frappe.bold(type_direction),
					frappe.bold(self.direction),
				)
			)

		requires_letter_number = cint(
			type_doc.get("requires_letter_number")
		)
		requires_letter_date = cint(
			type_doc.get("requires_letter_date")
		)

		self.type_requires_letter_number = (
			requires_letter_number
		)
		self.type_requires_letter_date = (
			requires_letter_date
		)
		self.type_requires_main_document = cint(
			type_doc.get("requires_main_document")
		)

		if self.direction == "Incoming":
			if (
				requires_letter_number
				and not self.external_letter_number
			):
				frappe.throw(
					_("External Letter Number is required.")
				)

			if (
				requires_letter_date
				and not self.external_letter_date
			):
				frappe.throw(
					_("External Letter Date is required.")
				)

		if self.direction == "Outgoing":
			if (
				requires_letter_number
				and not self.outgoing_letter_number
			):
				frappe.throw(
					_("Outgoing Letter Number is required.")
				)

			if (
				requires_letter_date
				and not self.outgoing_letter_date
			):
				frappe.throw(
					_("Outgoing Letter Date is required.")
				)

	def validate_due_date(self):
		if not self.due_date:
			return

		if getdate(self.due_date) < getdate(nowdate()):
			frappe.throw(
				_(
					"Due Date cannot be earlier than today."
				)
			)

	def validate_correspondence_links(self):
		rows = self.get("correspondence_links") or []
		seen = set()
		primary_rows = []

		for row in rows:
			linked_name = row.linked_correspondence

			if not linked_name:
				continue

			if linked_name == self.name:
				frappe.throw(
					_(
						"A correspondence cannot be linked "
						"to itself."
					),
					title=_("Invalid Correspondence Link"),
				)

			if linked_name in seen:
				frappe.throw(
					_(
						"Linked correspondence {0} is "
						"duplicated."
					).format(
						frappe.bold(linked_name)
					)
				)

			seen.add(linked_name)

			if not frappe.db.exists(
				"Murasalat Correspondence",
				linked_name,
			):
				frappe.throw(
					_(
						"Linked correspondence {0} "
						"does not exist."
					).format(
						frappe.bold(linked_name)
					)
				)

			if cint(row.is_primary_reference):
				primary_rows.append(row)

		if len(primary_rows) > 1:
			frappe.throw(
				_(
					"Only one linked correspondence can "
					"be the primary reference."
				)
			)

		if rows and not primary_rows:
			rows[0].is_primary_reference = 1

	def validate_required_main_document(self):
		if not cint(self.type_requires_main_document):
			return

		if not frappe.db.exists(
			"Murasalat Correspondence Document",
			{
				"correspondence": self.name,
				"is_main_document": 1,
				"docstatus": ["!=", 2],
			},
		):
			frappe.throw(
				_(
					"Add the main correspondence document "
					"before registration."
				),
				title=_("Main Document Required"),
			)

	def validate_closed_state(self):
		if self.workflow_state != CLOSED_WORKFLOW_STATE:
			return

		self.validate_no_active_referrals(
			_("Close")
		)

	def validate_no_active_referrals(self, action_label):
		if not self.name or self.is_new():
			return

		active_referrals = frappe.get_all(
			"Murasalat Referral",
			filters={
				"correspondence": self.name,
				"docstatus": ["!=", 2],
				"status": [
					"not in",
					list(FINAL_REFERRAL_STATUSES),
				],
			},
			pluck="name",
			limit=5,
		)

		if active_referrals:
			frappe.throw(
				_(
					"Cannot {0} this correspondence while "
					"active referrals exist: {1}"
				).format(
					action_label,
					", ".join(active_referrals),
				)
			)

	def set_closed_information(self):
		if self.workflow_state == CLOSED_WORKFLOW_STATE:
			if not self.closed_by:
				self.closed_by = frappe.session.user

			if not self.closed_on:
				self.closed_on = now()
		else:
			self.closed_by = None
			self.closed_on = None

	def validate_no_linked_transactions(self):
		linked_doctypes = (
			"Murasalat Correspondence Document",
			"Murasalat Referral",
			"Murasalat Referral Batch",
		)

		for doctype in linked_doctypes:
			if not frappe.db.exists("DocType", doctype):
				continue

			if frappe.db.exists(
				doctype,
				{"correspondence": self.name},
			):
				frappe.throw(
					_(
						"Cannot delete this correspondence "
						"because linked {0} records exist."
					).format(doctype)
				)

	def generate_correspondence_number(self):
		rule = self.get_numbering_rule()

		if not rule:
			year = getdate(nowdate()).year
			return make_autoname(
				f"MUR-{year}-.#####"
			)

		prefix = (
			rule.get("prefix")
			or "MUR"
		).strip()

		digits = cint(
			rule.get("number_of_digits")
			or rule.get("digits")
			or 5
		)

		digits = max(digits, 1)
		series_parts = [prefix.rstrip("-/ ")]

		if cint(rule.get("include_year")):
			if rule.get("year_type") == "Hijri":
				year = current_hijri_year(nowdate())
			else:
				year = getdate(nowdate()).year

			series_parts.append(str(year))

		series_prefix = "-".join(
			part for part in series_parts if part
		)

		return make_autoname(
			f"{series_prefix}-.{'#' * digits}"
		)

	def get_numbering_rule(self):
		if not frappe.db.exists(
			"DocType",
			"Murasalat Numbering Rule",
		):
			return None

		meta = frappe.get_meta(
			"Murasalat Numbering Rule"
		)

		fields = [
			"name",
			"prefix",
			"include_year",
			"year_type",
			"is_default",
		]

		if meta.has_field("number_of_digits"):
			fields.append("number_of_digits")

		if meta.has_field("digits"):
			fields.append("digits")

		filters = {}

		if meta.has_field("is_active"):
			filters["is_active"] = 1

		rules = frappe.get_all(
			"Murasalat Numbering Rule",
			filters=filters,
			fields=fields,
			order_by="is_default desc, modified desc",
		)

		best_rule = None
		best_score = -1

		for rule in rules:
			rule_doc = frappe.get_cached_doc(
				"Murasalat Numbering Rule",
				rule.name,
			)

			score = 0

			if rule_doc.meta.has_field(
				"correspondence_type"
			):
				rule_type = rule_doc.get(
					"correspondence_type"
				)

				if (
					rule_type
					and rule_type != self.correspondence_type
				):
					continue

				if rule_type:
					score += 4

			if rule_doc.meta.has_field("direction"):
				rule_direction = rule_doc.get("direction")

				if (
					rule_direction
					and rule_direction != self.direction
				):
					continue

				if rule_direction:
					score += 2

			if cint(rule_doc.get("is_default")):
				score += 1

			if score > best_score:
				best_rule = rule_doc
				best_score = score

		return best_rule