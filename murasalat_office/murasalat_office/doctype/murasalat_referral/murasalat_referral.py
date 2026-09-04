from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import date_diff, getdate, now, today

from murasalat_office.utils.hijri import (
	gregorian_to_hijri,
)
from murasalat_office.utils.profile import (
	get_current_user_profile,
)
from murasalat_office.utils.routing import (
	update_correspondence_routing_summary,
)


DRAFT_STATUS = "Draft"

ACTIVE_STATUSES = (
	"Sent",
	"Received",
	"In Progress",
)

FINAL_STATUSES = (
	"Completed",
	"Returned",
	"Withdrawn",
	"Cancelled",
)

ALLOWED_STATUSES = (
	"Draft",
	"Sent",
	"Received",
	"In Progress",
	"Completed",
	"Returned",
	"Withdrawn",
	"Cancelled",
)


class MurasalatReferral(Document):
	# -------------------------------------------------------------------------
	# Document lifecycle
	# -------------------------------------------------------------------------

	def before_validate(self):
		self.set_defaults()
		self.set_hijri_date()
		self.set_copy_semantics()
		self.set_overdue_values()

	def validate(self):
		self.validate_correspondence()
		self.validate_recipient()
		self.validate_dates()
		self.validate_parent_referral()
		self.validate_status()

	def on_update(self):
		"""
		on_update is also executed after inserting a new document,
		so a separate after_insert hook is not required.
		"""
		self.update_parent_correspondence()

	def on_update_after_submit(self):
		self.update_parent_correspondence()

	def before_cancel(self):
		self.status = "Cancelled"
		self.set_overdue_values()

	def on_cancel(self):
		self.update_parent_correspondence()

	def on_trash(self):
		"""
		Keep the correspondence name because after deletion the
		referral document is no longer available in the database.
		"""
		frappe.flags.murasalat_referral_correspondence = (
			self.get("correspondence")
		)

	def after_delete(self):
		correspondence = getattr(
			frappe.flags,
			"murasalat_referral_correspondence",
			None,
		)

		if correspondence:
			update_correspondence_routing_summary(
				correspondence
			)

	# -------------------------------------------------------------------------
	# Parent correspondence
	# -------------------------------------------------------------------------

	def update_parent_correspondence(self):
		if self.get("correspondence"):
			update_correspondence_routing_summary(
				self.correspondence
			)

	# -------------------------------------------------------------------------
	# Defaults
	# -------------------------------------------------------------------------

	def set_defaults(self):
		profile = (
			get_current_user_profile(
				frappe.session.user
			)
			or {}
		)

		# status must be initialized before set_overdue_values()
		if not self.get("status"):
			self.status = DRAFT_STATUS

		if not self.get("from_user"):
			self.from_user = frappe.session.user

		if not self.get("from_department"):
			self.from_department = (
				profile.get("default_department")
				or profile.get("department")
				or frappe.defaults.get_user_default(
					"Department"
				)
			)

		if not self.get("correspondence"):
			return

		correspondence = frappe.db.get_value(
			"Murasalat Correspondence",
			self.correspondence,
			[
				"priority_level",
				"owner_department",
				"docstatus",
			],
			as_dict=True,
		)

		if not correspondence:
			return

		if not self.get("priority_level"):
			self.priority_level = (
				correspondence.get("priority_level")
			)

		if not self.get("from_department"):
			self.from_department = (
				correspondence.get(
					"owner_department"
				)
			)

	# -------------------------------------------------------------------------
	# Hijri date
	# -------------------------------------------------------------------------

	def set_hijri_date(self):
		if self.meta.has_field("due_date_hijri"):
			self.due_date_hijri = (
				gregorian_to_hijri(
					self.get("due_date")
				)
			)

	# -------------------------------------------------------------------------
	# Copy behavior
	# -------------------------------------------------------------------------

	def set_copy_semantics(self):
		send_copy = bool(self.get("send_copy"))
		is_copy = bool(self.get("is_copy"))

		if send_copy:
			self.is_copy = 1
			is_copy = True

		if is_copy:
			self.send_copy = 1
			self.action_required = 0

		elif self.get("action_required") is None:
			self.action_required = 1

	# -------------------------------------------------------------------------
	# Overdue calculation
	# -------------------------------------------------------------------------

	def set_overdue_values(self):
		status = self.get("status") or DRAFT_STATUS
		due_date = self.get("due_date")

		if (
			status in ACTIVE_STATUSES
			and due_date
			and getdate(due_date) < getdate(today())
		):
			self.is_overdue = 1
			self.overdue_days = date_diff(
				today(),
				due_date,
			)
		else:
			self.is_overdue = 0
			self.overdue_days = 0

	# -------------------------------------------------------------------------
	# Validations
	# -------------------------------------------------------------------------

	def validate_correspondence(self):
		if not self.get("correspondence"):
			frappe.throw(
				_("Correspondence is required.")
			)

		correspondence = frappe.db.get_value(
			"Murasalat Correspondence",
			self.correspondence,
			[
				"name",
				"docstatus",
				"workflow_state",
			],
			as_dict=True,
		)

		if not correspondence:
			frappe.throw(
				_(
					"Correspondence {0} does not exist."
				).format(
					frappe.bold(
						self.correspondence
					)
				)
			)

		if correspondence.get("docstatus") != 1:
			frappe.throw(
				_(
					"Only registered correspondence "
					"can be referred."
				)
			)

		if (
			correspondence.get("workflow_state")
			== "Murasalat Closed"
		):
			frappe.throw(
				_(
					"Closed correspondence cannot "
					"be referred."
				)
			)

	def validate_recipient(self):
		recipient_type = self.get("recipient_type")

		if recipient_type not in (
			"User",
			"Department",
		):
			frappe.throw(
				_("Invalid Recipient Type.")
			)

		if recipient_type == "User":
			if not self.get("to_user"):
				frappe.throw(
					_("To User is required.")
				)

			self.to_department = None

		elif recipient_type == "Department":
			if not self.get("to_department"):
				frappe.throw(
					_("To Department is required.")
				)

			self.to_user = None

	def validate_dates(self):
		due_date = self.get("due_date")
		status = self.get("status") or DRAFT_STATUS

		if not due_date:
			return

		# Do not prevent editing an old Draft referral merely because
		# its existing due date has passed. Validate only new referrals
		# or when the due date itself is changed.
		due_date_changed = (
			self.is_new()
			or self.has_value_changed("due_date")
		)

		if (
			status == DRAFT_STATUS
			and due_date_changed
			and getdate(due_date) < getdate(today())
		):
			frappe.throw(
				_(
					"Due Date cannot be earlier "
					"than today."
				)
			)

	def validate_parent_referral(self):
		parent_referral = self.get("parent_referral")

		if not parent_referral:
			self.root_referral = None
			return

		if parent_referral == self.name:
			frappe.throw(
				_(
					"A referral cannot be its "
					"own parent."
				)
			)

		parent = frappe.db.get_value(
			"Murasalat Referral",
			parent_referral,
			[
				"name",
				"correspondence",
				"root_referral",
			],
			as_dict=True,
		)

		if not parent:
			frappe.throw(
				_("Parent Referral does not exist.")
			)

		if (
			parent.get("correspondence")
			!= self.get("correspondence")
		):
			frappe.throw(
				_(
					"Parent Referral must belong to "
					"the same correspondence."
				)
			)

		self.validate_parent_referral_cycle(
			parent_referral
		)

		self.root_referral = (
			parent.get("root_referral")
			or parent_referral
		)

	def validate_parent_referral_cycle(
		self,
		parent_referral,
	):
		"""
		Prevents circular chains such as:
		A -> B -> C -> A
		"""
		if self.is_new():
			return

		current_parent = parent_referral
		visited = set()

		while current_parent:
			if current_parent == self.name:
				frappe.throw(
					_(
						"Circular Parent Referral "
						"relationships are not allowed."
					)
				)

			if current_parent in visited:
				frappe.throw(
					_(
						"Circular Parent Referral "
						"relationships are not allowed."
					)
				)

			visited.add(current_parent)

			current_parent = frappe.db.get_value(
				"Murasalat Referral",
				current_parent,
				"parent_referral",
			)

	def validate_status(self):
		status = self.get("status") or DRAFT_STATUS

		if status not in ALLOWED_STATUSES:
			frappe.throw(
				_(
					"Invalid referral status: {0}."
				).format(
					frappe.bold(status)
				)
			)

	# -------------------------------------------------------------------------
	# Status actions
	# -------------------------------------------------------------------------

	@frappe.whitelist()
	def send_referral(self):
		self.check_permission("write")

		status = self.get("status") or DRAFT_STATUS

		if status != DRAFT_STATUS:
			frappe.throw(
				_(
					"Only draft referrals can be sent."
				)
			)

		current_time = now()

		self.status = "Sent"
		self.set_optional_field(
			"sent_on",
			current_time,
		)
		self.set_optional_field(
			"sent_by",
			frappe.session.user,
		)

		self.set_overdue_values()
		self.save()

		return self.as_dict()

	@frappe.whitelist()
	def mark_received(self):
		self.ensure_current_recipient()

		if self.get("status") != "Sent":
			frappe.throw(
				_(
					"Only sent referrals can be "
					"marked as received."
				)
			)

		current_time = now()

		self.status = "Received"

		self.set_optional_field(
			"received_on",
			current_time,
		)
		self.set_optional_field(
			"received_by",
			frappe.session.user,
		)
		self.set_optional_field(
			"accepted_on",
			current_time,
		)
		self.set_optional_field(
			"accepted_by",
			frappe.session.user,
		)

		self.set_overdue_values()
		self.save()

		return self.as_dict()

	@frappe.whitelist()
	def start_processing(self):
		self.ensure_current_recipient()

		if self.get("status") not in (
			"Sent",
			"Received",
		):
			frappe.throw(
				_(
					"Only sent or received referrals "
					"can be started."
				)
			)

		current_time = now()

		if not self.get("received_on"):
			self.set_optional_field(
				"received_on",
				current_time,
			)
			self.set_optional_field(
				"received_by",
				frappe.session.user,
			)

		self.status = "In Progress"

		self.set_optional_field(
			"started_on",
			current_time,
		)
		self.set_optional_field(
			"started_by",
			frappe.session.user,
		)

		self.set_overdue_values()
		self.save()

		return self.as_dict()

	@frappe.whitelist()
	def complete_referral(
		self,
		completion_notes=None,
	):
		self.ensure_current_recipient()

		if self.get("status") not in ACTIVE_STATUSES:
			frappe.throw(
				_(
					"This referral cannot be completed "
					"from its current status."
				)
			)

		if (
			self.get("action_required")
			and not completion_notes
		):
			frappe.throw(
				_("Completion Notes are required.")
			)

		current_time = now()

		self.status = "Completed"

		self.set_optional_field(
			"completed_on",
			current_time,
		)
		self.set_optional_field(
			"completed_by",
			frappe.session.user,
		)

		if completion_notes is not None:
			self.set_optional_field(
				"completion_notes",
				completion_notes,
			)

		self.set_overdue_values()
		self.save()

		return self.as_dict()

	@frappe.whitelist()
	def return_referral(
		self,
		reason=None,
	):
		self.ensure_current_recipient()

		if self.get("status") not in ACTIVE_STATUSES:
			frappe.throw(
				_(
					"This referral cannot be returned "
					"from its current status."
				)
			)

		if not reason:
			frappe.throw(
				_("Return Reason is required.")
			)

		current_time = now()

		self.status = "Returned"

		self.set_optional_field(
			"returned_on",
			current_time,
		)
		self.set_optional_field(
			"returned_by",
			frappe.session.user,
		)
		self.set_optional_field(
			"return_reason",
			reason,
		)

		self.set_overdue_values()
		self.save()

		return self.as_dict()

	@frappe.whitelist()
	def withdraw_referral(
		self,
		reason=None,
	):
		if (
			self.get("from_user")
			!= frappe.session.user
			and not has_manager_role()
		):
			frappe.throw(
				_(
					"Only the sender or a Murasalat "
					"Manager can withdraw this referral."
				),
				frappe.PermissionError,
			)

		if self.get("status") not in (
			"Sent",
			"Received",
		):
			frappe.throw(
				_(
					"Only sent or received referrals "
					"can be withdrawn."
				)
			)

		if not reason:
			frappe.throw(
				_("Withdrawal Reason is required.")
			)

		current_time = now()

		self.status = "Withdrawn"

		self.set_optional_field(
			"withdrawn_on",
			current_time,
		)
		self.set_optional_field(
			"withdrawn_by",
			frappe.session.user,
		)
		self.set_optional_field(
			"withdrawal_reason",
			reason,
		)

		self.set_overdue_values()
		self.save()

		return self.as_dict()

	# -------------------------------------------------------------------------
	# Permissions
	# -------------------------------------------------------------------------

	def ensure_current_recipient(self):
		user = frappe.session.user

		profile = (
			get_current_user_profile(user)
			or {}
		)

		recipient_type = self.get(
			"recipient_type"
		)

		if (
			recipient_type == "User"
			and self.get("to_user") == user
		):
			return

		user_department = (
			profile.get("default_department")
			or profile.get("department")
		)

		if (
			recipient_type == "Department"
			and user_department
			and user_department
			== self.get("to_department")
		):
			return

		if has_manager_role():
			return

		frappe.throw(
			_(
				"Only the referral recipient can "
				"perform this action."
			),
			frappe.PermissionError,
		)

	# -------------------------------------------------------------------------
	# Utility methods
	# -------------------------------------------------------------------------

	def set_optional_field(
		self,
		fieldname,
		value,
	):
		"""
		Set an optional value only when the field exists in the
		Murasalat Referral DocType.
		"""
		if self.meta.has_field(fieldname):
			self.set(fieldname, value)


def has_manager_role():
	roles = set(
		frappe.get_roles(
			frappe.session.user
		)
	)

	manager_roles = {
		"Murasalat Manager",
		"Murasalat System Manager",
		"System Manager",
	}

	return bool(
		roles.intersection(manager_roles)
	)
