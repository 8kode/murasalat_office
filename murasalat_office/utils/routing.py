from __future__ import annotations

import frappe
from frappe.utils import getdate, nowdate


COMPLETED_STATUSES = {
	"Completed",
}

INACTIVE_STATUSES = {
	"Withdrawn",
	"Cancelled",
}


def sync_correspondence_summary(doc, method=None):
	correspondence = doc.get("correspondence")

	if not correspondence:
		return

	if not frappe.db.exists(
		"Murasalat Correspondence",
		correspondence,
	):
		return

	update_correspondence_routing_summary(
		correspondence
	)


def update_correspondence_routing_summary(
	correspondence: str,
):
	referrals = frappe.get_all(
		"Murasalat Referral",
		filters={
			"correspondence": correspondence,
			"docstatus": ["!=", 2],
		},
		fields=[
			"name",
			"status",
			"due_date",
			"sent_on",
			"creation",
			"modified",
		],
	)

	today = getdate(nowdate())

	active_count = 0
	pending_count = 0
	completed_count = 0
	overdue_count = 0

	last_referred_values = []
	last_activity_values = []

	for referral in referrals:
		status = referral.status or "Draft"

		if status in COMPLETED_STATUSES:
			completed_count += 1

		elif status in INACTIVE_STATUSES:
			pass

		else:
			active_count += 1
			pending_count += 1

			if (
				referral.due_date
				and getdate(referral.due_date) < today
			):
				overdue_count += 1

		if referral.sent_on:
			last_referred_values.append(
				referral.sent_on
			)
		elif referral.creation:
			last_referred_values.append(
				referral.creation
			)

		if referral.modified:
			last_activity_values.append(
				referral.modified
			)

	routing_status = get_routing_status(
		total=len(referrals),
		active=active_count,
		completed=completed_count,
		overdue=overdue_count,
	)

	frappe.db.set_value(
		"Murasalat Correspondence",
		correspondence,
		{
			"routing_status": routing_status,
			"active_referral_count": active_count,
			"pending_referral_count": pending_count,
			"completed_referral_count": completed_count,
			"overdue_referral_count": overdue_count,
			"last_referred_on": (
				max(last_referred_values)
				if last_referred_values
				else None
			),
			"last_activity_on": (
				max(last_activity_values)
				if last_activity_values
				else None
			),
		},
		update_modified=False,
	)


def get_routing_status(
	total: int,
	active: int,
	completed: int,
	overdue: int,
) -> str:
	if total == 0:
		return "No Referrals"

	if overdue > 0:
		return "Overdue"

	if active > 0 and completed > 0:
		return "Partially Completed"

	if active > 0:
		return "Active"

	if completed > 0:
		return "Completed"

	return "Inactive"