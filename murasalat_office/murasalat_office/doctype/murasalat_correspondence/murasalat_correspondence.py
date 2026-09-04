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
from murasalat_office.utils.profile import get_current_user_profile


CLOSED_WORKFLOW_STATE = "Murasalat Closed"

FINAL_REFERRAL_STATUSES = {
	"Completed",
	"Returned",
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

DIRECTION_ALLOW_FIELDS = {
	"Internal": "allow_internal",
	"Incoming": "allow_incoming",
	"Outgoing": "allow_outgoing",
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
		self.validate_required_main_document()
		self.validate_closed_state()
		self.set_closed_information()
		self.set_identification_values()

	def before_cancel(self):
		self.validate_no_active_referrals(_("Cancel"))

	def on_trash(self):
		self.validate_no_linked_transactions()

	# -------------------------------------------------------------------------
	# Defaults
	# -------------------------------------------------------------------------

	def set_defaults(self):
		profile = get_current_user_profile() or {}

		profile_company = (
			profile.get("company")
			or profile.get("default_company")
		)

		profile_department = (
			profile.get("department")
			or profile.get("default_department")
		)

		profile_employee = (
			profile.get("employee")
			or profile.get("employee_id")
		)

		if not self.company:
			self.company = (
				profile_company
				or frappe.defaults.get_user_default("Company")
				or self.get_settings_value("default_company")
			)

		if not self.owner_department:
			self.owner_department = (
				profile_department
				or frappe.defaults.get_user_default("Department")
				or self.get_settings_value("default_department")
			)

		if not self.confidentiality_level:
			self.confidentiality_level = self.get_settings_value(
				"default_confidentiality"
			)

		if not self.priority_level:
			self.priority_level = self.get_settings_value(
				"default_priority"
			)

		if self.direction == "Internal":
			if not self.prepared_by:
				self.prepared_by = frappe.session.user

			if not self.prepared_by_employee and profile_employee:
				self.prepared_by_employee = profile_employee

			if not self.origin_department:
				self.origin_department = self.owner_department

		elif self.direction == "Outgoing":
			if not self.outgoing_from_department:
				self.outgoing_from_department = (
					self.owner_department
				)

		elif self.direction == "Incoming":
			if not self.incoming_to_department:
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

		if not meta.issingle:
			return None

		if not meta.has_field(fieldname):
			return None

		return frappe.db.get_single_value(
			"Murasalat Settings",
			fieldname,
		)

	# -------------------------------------------------------------------------
	# Direction fields
	# -------------------------------------------------------------------------

	def clear_irrelevant_direction_fields(self):
		selected_fields = set(
			DIRECTION_FIELDS.get(self.direction, ())
		)

		for fields in DIRECTION_FIELDS.values():
			for fieldname in fields:
				if fieldname not in selected_fields:
					self.set(fieldname, None)

	def validate_direction(self):
		if self.direction not in DIRECTION_FIELDS:
			frappe.throw(
				_(
					"Please select a valid correspondence "
					"direction."
				)
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

	# -------------------------------------------------------------------------
	# Hijri dates and identification
	# -------------------------------------------------------------------------

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

	# -------------------------------------------------------------------------
	# Correspondence Type
	# -------------------------------------------------------------------------

	def validate_correspondence_type(self):
		if not self.correspondence_type:
			self.type_requires_letter_number = 0
			self.type_requires_letter_date = 0
			self.type_requires_main_document = 0
			return

		type_doc = frappe.get_cached_doc(
			"Murasalat Correspondence Type",
			self.correspondence_type,
		)

		if (
			type_doc.meta.has_field("is_active")
			and not cint(type_doc.get("is_active"))
		):
			frappe.throw(
				_(
					"Correspondence Type {0} is inactive."
				).format(
					frappe.bold(
						self.correspondence_type
					)
				)
			)

		self.validate_type_direction(type_doc)

		requires_letter_number = cint(
			type_doc.get("requires_letter_number")
		)

		requires_letter_date = cint(
			type_doc.get("requires_letter_date")
		)

		requires_main_document = cint(
			type_doc.get("requires_main_document")
		)

		self.type_requires_letter_number = (
			requires_letter_number
		)

		self.type_requires_letter_date = (
			requires_letter_date
		)

		self.type_requires_main_document = (
			requires_main_document
		)

		if self.direction == "Incoming":
			if (
				requires_letter_number
				and not self.external_letter_number
			):
				frappe.throw(
					_(
						"External Letter Number is "
						"required."
					)
				)

			if (
				requires_letter_date
				and not self.external_letter_date
			):
				frappe.throw(
					_(
						"External Letter Date is required."
					)
				)

		elif self.direction == "Outgoing":
			if (
				requires_letter_number
				and not self.outgoing_letter_number
			):
				frappe.throw(
					_(
						"Outgoing Letter Number is "
						"required."
					)
				)

			if (
				requires_letter_date
				and not self.outgoing_letter_date
			):
				frappe.throw(
					_(
						"Outgoing Letter Date is required."
					)
				)

	def validate_type_direction(self, type_doc):
		"""
		Supports either one of these Correspondence Type designs:

		1. A Select field named `direction`.
		2. Three Check fields:
		   - allow_internal
		   - allow_incoming
		   - allow_outgoing
		"""

		if type_doc.meta.has_field("direction"):
			type_direction = type_doc.get("direction")

			if (
				type_direction
				and type_direction != self.direction
			):
				frappe.throw(
					_(
						"Correspondence Type {0} is "
						"configured for direction {1}, "
						"not {2}."
					).format(
						frappe.bold(
							self.correspondence_type
						),
						frappe.bold(type_direction),
						frappe.bold(self.direction),
					)
				)

			return

		allow_field = DIRECTION_ALLOW_FIELDS.get(
			self.direction
		)

		if (
			allow_field
			and type_doc.meta.has_field(allow_field)
			and not cint(type_doc.get(allow_field))
		):
			frappe.throw(
				_(
					"Correspondence Type {0} is not "
					"allowed for direction {1}."
				).format(
					frappe.bold(
						self.correspondence_type
					),
					frappe.bold(self.direction),
				)
			)

	# -------------------------------------------------------------------------
	# Date validation
	# -------------------------------------------------------------------------

	def validate_due_date(self):
		if not self.due_date:
			return

		# Do not prevent saving an existing overdue correspondence
		# unless the Due Date itself was changed.
		if (
			not self.is_new()
			and not self.has_value_changed("due_date")
		):
			return

		if getdate(self.due_date) < getdate(nowdate()):
			frappe.throw(
				_(
					"Due Date cannot be earlier than today."
				)
			)

	# -------------------------------------------------------------------------
	# Correspondence links
	# -------------------------------------------------------------------------

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
					title=_(
						"Invalid Correspondence Link"
					),
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
			first_valid_row = next(
				(
					row
					for row in rows
					if row.linked_correspondence
				),
				None,
			)

			if first_valid_row:
				first_valid_row.is_primary_reference = 1

	# -------------------------------------------------------------------------
	# Main document
	# -------------------------------------------------------------------------

	def validate_required_main_document(self):
		if not cint(self.type_requires_main_document):
			return

		if not self.name or self.is_new():
			frappe.throw(
				_(
					"Save the correspondence and add the "
					"main correspondence document before "
					"registration."
				),
				title=_("Main Document Required"),
			)

		main_document_exists = frappe.db.exists(
			"Murasalat Correspondence Document",
			{
				"correspondence": self.name,
				"is_main_document": 1,
				"docstatus": ["!=", 2],
			},
		)

		if not main_document_exists:
			frappe.throw(
				_(
					"Add the main correspondence document "
					"before registration."
				),
				title=_("Main Document Required"),
			)

	# -------------------------------------------------------------------------
	# Closing and cancellation
	# -------------------------------------------------------------------------

	def validate_closed_state(self):
		if self.workflow_state != CLOSED_WORKFLOW_STATE:
			return

		self.validate_no_active_referrals(_("Close"))

	def validate_no_active_referrals(self, action_label):
		if not self.name or self.is_new():
			return

		if not frappe.db.exists(
			"DocType",
			"Murasalat Referral",
		):
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
					).format(
						frappe.bold(doctype)
					)
				)

	# -------------------------------------------------------------------------
	# Numbering
	# -------------------------------------------------------------------------

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

		series_parts = [
			prefix.rstrip("-/ ")
		]

		if cint(rule.get("include_year")):
			if rule.get("year_type") == "Hijri":
				year = current_hijri_year(
					nowdate()
				)
			else:
				year = getdate(nowdate()).year

			series_parts.append(str(year))

		series_prefix = "-".join(
			part
			for part in series_parts
			if part
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

		required_fields = ["name"]

		optional_fields = (
			"prefix",
			"include_year",
			"year_type",
			"is_default",
			"number_of_digits",
			"digits",
			"is_active",
			"correspondence_type",
			"direction",
		)

		fields = list(required_fields)

		for fieldname in optional_fields:
			if meta.has_field(fieldname):
				fields.append(fieldname)

		filters = {}

		if meta.has_field("is_active"):
			filters["is_active"] = 1

		order_parts = []

		if meta.has_field("is_default"):
			order_parts.append("is_default desc")

		order_parts.append("modified desc")

		rules = frappe.get_all(
			"Murasalat Numbering Rule",
			filters=filters,
			fields=fields,
			order_by=", ".join(order_parts),
		)

		best_rule = None
		best_score = -1

		for rule in rules:
			score = 0

			rule_type = rule.get(
				"correspondence_type"
			)

			if (
				rule_type
				and rule_type != self.correspondence_type
			):
				continue

			if rule_type:
				score += 4

			rule_direction = rule.get("direction")

			if (
				rule_direction
				and rule_direction != self.direction
			):
				continue

			if rule_direction:
				score += 2

			if cint(rule.get("is_default")):
				score += 1

			if score > best_score:
				best_rule = rule
				best_score = score

		return best_rule
