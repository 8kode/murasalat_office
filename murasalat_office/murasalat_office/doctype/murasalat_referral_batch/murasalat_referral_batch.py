from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, now, nowdate


CLOSED_WORKFLOW_STATE = "Murasalat Closed"


class MurasalatReferralBatch(Document):
	def before_validate(self):
		self.set_defaults()
		self.apply_row_defaults()

	def validate(self):
		self.validate_correspondence()
		self.validate_recipients()

	def before_submit(self):
		self.validate_correspondence()
		self.validate_recipients()
		self.create_referrals()

		self.status = "Completed"
		self.processed_on = now()
		self.created_referrals = len(
			[
				row
				for row in self.recipients
				if row.created_referral
			]
		)

	def before_cancel(self):
		created = [
			row.created_referral
			for row in self.recipients
			if row.created_referral
		]

		if created:
			frappe.throw(
				_(
					"This referral batch cannot be cancelled "
					"because it already created referrals: {0}"
				).format(", ".join(created))
			)

	def set_defaults(self):
		if not self.from_user:
			self.from_user = frappe.session.user

		if self.correspondence:
			values = frappe.db.get_value(
				"Murasalat Correspondence",
				self.correspondence,
				[
					"owner_department",
					"priority_level",
				],
				as_dict=True,
			)

			if values:
				if not self.from_department:
					self.from_department = (
						values.owner_department
					)

				if not self.default_priority_level:
					self.default_priority_level = (
						values.priority_level
					)

	def apply_row_defaults(self):
		for row in self.get("recipients") or []:
			if (
				not row.routing_purpose
				and self.default_routing_purpose
			):
				row.routing_purpose = (
					self.default_routing_purpose
				)

			if (
				not row.priority_level
				and self.default_priority_level
			):
				row.priority_level = (
					self.default_priority_level
				)

			if (
				not row.due_date
				and self.default_due_date
			):
				row.due_date = self.default_due_date

	def validate_correspondence(self):
		if not self.correspondence:
			return

		correspondence = frappe.get_doc(
			"Murasalat Correspondence",
			self.correspondence,
		)

		if correspondence.docstatus != 1:
			frappe.throw(
				_(
					"Register the correspondence before "
					"sending referrals."
				)
			)

		if (
			correspondence.workflow_state
			== CLOSED_WORKFLOW_STATE
		):
			frappe.throw(
				_(
					"Cannot create referrals for a closed "
					"correspondence."
				)
			)

	def validate_recipients(self):
		rows = self.get("recipients") or []

		if not rows:
			frappe.throw(
				_("Add at least one referral recipient.")
			)

		seen = set()

		for row in rows:
			if row.recipient_type == "User":
				if not row.to_user:
					frappe.throw(
						_(
							"Row {0}: To User is required."
						).format(row.idx)
					)

				row.to_department = None
				key = ("User", row.to_user)

			elif row.recipient_type == "Department":
				if not row.to_department:
					frappe.throw(
						_(
							"Row {0}: To Department is "
							"required."
						).format(row.idx)
					)

				row.to_user = None
				key = (
					"Department",
					row.to_department,
				)

			else:
				frappe.throw(
					_(
						"Row {0}: Select a valid "
						"Recipient Type."
					).format(row.idx)
				)

			if not row.routing_purpose:
				frappe.throw(
					_(
						"Row {0}: Routing Purpose is "
						"required."
					).format(row.idx)
				)

			if (
				row.due_date
				and getdate(row.due_date)
				< getdate(nowdate())
			):
				frappe.throw(
					_(
						"Row {0}: Due Date cannot be "
						"earlier than today."
					).format(row.idx)
				)

			if key in seen:
				frappe.throw(
					_(
						"Row {0}: The same recipient "
						"was added more than once."
					).format(row.idx)
				)

			seen.add(key)

	def create_referrals(self):
		referral_meta = frappe.get_meta(
			"Murasalat Referral"
		)

		for row in self.recipients:
			if row.created_referral:
				frappe.throw(
					_(
						"Row {0} already created referral "
						"{1}."
					).format(
						row.idx,
						row.created_referral,
					)
				)

			payload = {
				"doctype": "Murasalat Referral",
				"correspondence": self.correspondence,
				"referral_batch": self.name,
				"from_user": self.from_user,
				"from_department": self.from_department,
				"recipient_type": row.recipient_type,
				"to_user": row.to_user,
				"to_department": row.to_department,
				"routing_purpose": row.routing_purpose,
				"priority_level": row.priority_level,
				"due_date": row.due_date,
				"instructions": row.instructions,
				"paper_correspondence": (
					row.paper_correspondence
				),
				"send_copy": row.send_copy,
				"for_follow_up": row.for_follow_up,
				"status": "Sent",
				"sent_on": now(),
			}

			safe_payload = {
				key: value
				for key, value in payload.items()
				if key == "doctype"
				or referral_meta.has_field(key)
			}

			referral = frappe.get_doc(safe_payload)
			referral.insert()

			row.created_referral = referral.name