from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, now, today

from murasalat_office.murasalat_office.doctype.murasalat_correspondence.murasalat_correspondence import (
    CLOSED_STATE,
    get_current_user_profile,
)
from murasalat_office.utils.dates import gregorian_to_hijri


class MurasalatReferral(Document):
    def before_validate(self):
        self.set_defaults()
        self.set_hijri_date()
        self.set_copy_semantics()

    def validate(self):
        self.validate_correspondence()
        self.validate_recipient()
        self.validate_dates()
        self.validate_active_link_values()
        self.validate_parent_referral()
        self.validate_workflow_transition()
        self.apply_transition_metadata()

    def set_defaults(self):
        profile = get_current_user_profile()

        if not self.from_user:
            self.from_user = frappe.session.user
        if profile and not self.from_department:
            self.from_department = profile.default_department

        if self.correspondence and not self.priority_level:
            self.priority_level = frappe.db.get_value(
                "Murasalat Correspondence",
                self.correspondence,
                "priority_level",
            )

    def set_hijri_date(self):
        self.due_date_hijri = gregorian_to_hijri(self.due_date)

    def set_copy_semantics(self):
        if self.send_copy:
            self.action_required = 0
        elif self.action_required is None:
            self.action_required = 1

    def validate_correspondence(self):
        correspondence = frappe.get_doc("Murasalat Correspondence", self.correspondence)

        if correspondence.docstatus != 1:
            frappe.throw(_("Only registered correspondence can be referred."))
        if correspondence.workflow_state == CLOSED_STATE:
            frappe.throw(_("Closed correspondence cannot be referred."))

    def validate_recipient(self):
        if self.recipient_type == "User":
            if not self.to_user:
                frappe.throw(_("To User is required."))
            self.to_department = None
        elif self.recipient_type == "Department":
            if not self.to_department:
                frappe.throw(_("To Department is required."))
            self.to_user = None
        else:
            frappe.throw(_("Invalid Recipient Type."))

    def validate_dates(self):
        if self.is_new() and self.due_date and getdate(self.due_date) < getdate(today()):
            frappe.throw(_("Due Date cannot be earlier than today."))

    def validate_active_link_values(self):
        for doctype, name in (
            ("Murasalat Routing Purpose", self.routing_purpose),
            ("Murasalat Priority Level", self.priority_level),
        ):
            if name and not frappe.db.get_value(doctype, name, "is_active"):
                frappe.throw(_("{0} {1} is inactive.").format(doctype, name))

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
            frappe.throw(_("Parent Referral must belong to the same correspondence."))

        self.root_referral = parent.root_referral or self.parent_referral

    def validate_workflow_transition(self):
        old = self._doc_before_save
        if not old or old.workflow_state == self.workflow_state:
            return

        target_state = self.workflow_state
        if target_state in {"Murasalat Referral Received", "Murasalat Referral In Progress", "Murasalat Referral Completed", "Murasalat Referral Returned"}:
            self.ensure_current_recipient()

        if target_state == "Murasalat Referral Withdrawn":
            if self.from_user != frappe.session.user and not has_manager_role():
                frappe.throw(
                    _("Only the sender or a Murasalat Manager can withdraw this referral."),
                    frappe.PermissionError,
                )

    def apply_transition_metadata(self):
        old_state = self._doc_before_save.workflow_state if self._doc_before_save else None
        if old_state == self.workflow_state:
            return

        current_time = now()
        current_user = frappe.session.user

        if self.workflow_state == "Murasalat Referral Sent":
            self.sent_on = self.sent_on or current_time
        elif self.workflow_state == "Murasalat Referral Received":
            self.received_on = self.received_on or current_time
            self.accepted_on = self.accepted_on or current_time
        elif self.workflow_state == "Murasalat Referral In Progress":
            self.opened_on = self.opened_on or current_time
            self.received_on = self.received_on or current_time
        elif self.workflow_state == "Murasalat Referral Completed":
            self.completed_on = self.completed_on or current_time
            self.completed_by = self.completed_by or current_user
        elif self.workflow_state == "Murasalat Referral Returned":
            self.returned_on = self.returned_on or current_time
            self.returned_by = self.returned_by or current_user
        elif self.workflow_state == "Murasalat Referral Withdrawn":
            self.withdrawn_on = self.withdrawn_on or current_time
            self.withdrawn_by = self.withdrawn_by or current_user

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
            {"Murasalat Manager", "Murasalat System Manager", "System Manager"}
        )
    )
