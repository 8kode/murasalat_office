from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import date_diff, getdate, now, today

from murasalat_office.murasalat_office.doctype.murasalat_correspondence.murasalat_correspondence import (
    get_current_user_profile,
    update_correspondence_routing_summary,
)
from murasalat_office.utils.hijri import gregorian_to_hijri


ACTIVE_STATUSES = ("Sent", "Received", "In Progress")
FINAL_STATUSES = ("Completed", "Returned", "Withdrawn", "Cancelled")


class MurasalatReferral(Document):
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

    def after_insert(self):
        update_correspondence_routing_summary(self.correspondence)

    def on_update(self):
        update_correspondence_routing_summary(self.correspondence)

    def on_trash(self):
        correspondence = self.correspondence
        frappe.flags.murasalat_update_correspondence = correspondence

    def after_delete(self):
        correspondence = getattr(
            frappe.flags,
            "murasalat_update_correspondence",
            None,
        )

        if correspondence:
            update_correspondence_routing_summary(correspondence)

    def set_defaults(self):
        profile = get_current_user_profile()

        if not self.from_user:
            self.from_user = frappe.session.user

        if profile and not self.from_department:
            self.from_department = profile.default_department

        if self.correspondence:
            correspondence = frappe.db.get_value(
                "Murasalat Correspondence",
                self.correspondence,
                ["priority_level", "docstatus"],
                as_dict=True,
            )

            if correspondence:
                self.priority_level = (
                    self.priority_level
                    or correspondence.priority_level
                )

    def set_hijri_date(self):
        self.due_date_hijri = gregorian_to_hijri(self.due_date)

    def set_copy_semantics(self):
        if self.send_copy:
            self.is_copy = 1

        if self.is_copy:
            self.send_copy = 1
            self.action_required = 0
        elif self.action_required is None:
            self.action_required = 1

    def set_overdue_values(self):
        if (
            self.status in ACTIVE_STATUSES
            and self.due_date
            and getdate(self.due_date) < getdate(today())
        ):
            self.is_overdue = 1
            self.overdue_days = date_diff(today(), self.due_date)
        else:
            self.is_overdue = 0
            self.overdue_days = 0

    def validate_correspondence(self):
        if not self.correspondence:
            frappe.throw(_("Correspondence is required."))

        correspondence = frappe.get_doc(
            "Murasalat Correspondence",
            self.correspondence,
        )

        if correspondence.docstatus != 1:
            frappe.throw(
                _("Only registered correspondence can be referred.")
            )

        if correspondence.workflow_state == "Murasalat Closed":
            frappe.throw(_("Closed correspondence cannot be referred."))

    def validate_recipient(self):
        if self.recipient_type not in ("User", "Department"):
            frappe.throw(_("Invalid Recipient Type."))

        if self.recipient_type == "User":
            if not self.to_user:
                frappe.throw(_("To User is required."))

            self.to_department = None

        if self.recipient_type == "Department":
            if not self.to_department:
                frappe.throw(_("To Department is required."))

            self.to_user = None

    def validate_dates(self):
        if (
            self.status == "Draft"
            and self.due_date
            and getdate(self.due_date) < getdate(today())
        ):
            frappe.throw(
                _("Due Date cannot be earlier than today.")
            )

    def validate_parent_referral(self):
        if not self.parent_referral:
            return

        if self.parent_referral == self.name:
            frappe.throw(_("A referral cannot be its own parent."))

        parent = frappe.db.get_value(
            "Murasalat Referral",
            self.parent_referral,
            ["correspondence", "root_referral"],
            as_dict=True,
        )

        if not parent:
            frappe.throw(_("Parent Referral does not exist."))

        if parent.correspondence != self.correspondence:
            frappe.throw(
                _("Parent Referral must belong to the same correspondence.")
            )

        self.root_referral = (
            parent.root_referral or self.parent_referral
        )

    def validate_status(self):
        allowed = (
            "Draft",
            "Sent",
            "Received",
            "In Progress",
            "Completed",
            "Returned",
            "Withdrawn",
            "Cancelled",
        )

        if self.status not in allowed:
            frappe.throw(_("Invalid referral status."))

    @frappe.whitelist()
    def send_referral(self):
        self.check_permission("write")

        if self.status != "Draft":
            frappe.throw(_("Only draft referrals can be sent."))

        self.status = "Sent"
        self.sent_on = now()
        self.save()

        return self.as_dict()

    @frappe.whitelist()
    def mark_received(self):
        self.ensure_current_recipient()

        if self.status != "Sent":
            frappe.throw(
                _("Only sent referrals can be marked as received.")
            )

        self.status = "Received"
        self.received_on = now()
        self.accepted_on = now()
        self.save()

        return self.as_dict()

    @frappe.whitelist()
    def start_processing(self):
        self.ensure_current_recipient()

        if self.status not in ("Sent", "Received"):
            frappe.throw(
                _("Only sent or received referrals can be started.")
            )

        if not self.received_on:
            self.received_on = now()

        self.status = "In Progress"
        self.save()

        return self.as_dict()

    @frappe.whitelist()
    def complete_referral(self, completion_notes=None):
        self.ensure_current_recipient()

        if self.status not in ("Sent", "Received", "In Progress"):
            frappe.throw(
                _("This referral cannot be completed from its current status.")
            )

        if self.action_required and not completion_notes:
            frappe.throw(
                _("Completion Notes are required.")
            )

        self.status = "Completed"
        self.completed_on = now()
        self.completed_by = frappe.session.user
        self.completion_notes = completion_notes
        self.save()

        return self.as_dict()

    @frappe.whitelist()
    def return_referral(self, reason):
        self.ensure_current_recipient()

        if self.status not in ("Sent", "Received", "In Progress"):
            frappe.throw(
                _("This referral cannot be returned from its current status.")
            )

        if not reason:
            frappe.throw(_("Return Reason is required."))

        self.status = "Returned"
        self.returned_on = now()
        self.returned_by = frappe.session.user
        self.return_reason = reason
        self.save()

        return self.as_dict()

    @frappe.whitelist()
    def withdraw_referral(self, reason):
        if self.from_user != frappe.session.user and not has_manager_role():
            frappe.throw(
                _("Only the sender or a Murasalat Manager can withdraw this referral."),
                frappe.PermissionError,
            )

        if self.status not in ("Sent", "Received"):
            frappe.throw(
                _("Only sent or received referrals can be withdrawn.")
            )

        if not reason:
            frappe.throw(_("Withdrawal Reason is required."))

        self.status = "Withdrawn"
        self.withdrawn_on = now()
        self.withdrawn_by = frappe.session.user
        self.withdrawal_reason = reason
        self.save()

        return self.as_dict()

    def ensure_current_recipient(self):
        user = frappe.session.user
        profile = get_current_user_profile(user)

        if self.recipient_type == "User" and self.to_user == user:
            return

        if (
            self.recipient_type == "Department"
            and profile
            and profile.default_department == self.to_department
        ):
            return

        if has_manager_role():
            return

        frappe.throw(
            _("Only the referral recipient can perform this action."),
            frappe.PermissionError,
        )


def has_manager_role():
    roles = set(frappe.get_roles(frappe.session.user))

    return bool(
        roles.intersection(
            {
                "Murasalat Manager",
                "Murasalat System Manager",
                "System Manager",
            }
        )
    )