from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.naming import getseries
from frappe.utils import cint, getdate, now, today

from murasalat_office.utils.dates import get_hijri_year, gregorian_to_hijri


ACTIVE_REFERRAL_STATES = ("Murasalat Referral Sent", "Murasalat Referral Received", "Murasalat Referral In Progress")
CLOSED_STATE = "Murasalat Closed"


class MurasalatCorrespondence(Document):
    def before_validate(self):
        self.set_defaults()
        self.set_direction_defaults()
        self.set_hijri_dates()

    def validate(self):
        self.validate_direction()
        self.validate_correspondence_type()
        self.validate_active_link_values()
        self.validate_due_date()
        self.validate_correspondence_links()
        self.validate_closed_state()

    def before_submit(self):
        self.validate_registration_requirements()
        self.issue_correspondence_number()

        if not self.registered_by:
            self.registered_by = frappe.session.user
        if not self.registered_on:
            self.registered_on = now()

    def on_submit(self):
        self.db_set("barcode", self.correspondence_number, update_modified=False)
        self.db_set("qr_code", self.correspondence_number, update_modified=False)

    def before_cancel(self):
        active_referrals = frappe.db.count(
            "Murasalat Referral",
            {
                "correspondence": self.name,
                "workflow_state": ["in", list(ACTIVE_REFERRAL_STATES)],
            },
        )
        if active_referrals:
            frappe.throw(
                _(
                    "The correspondence cannot be cancelled while it has active referrals. "
                    "Withdraw, return, complete, or cancel the active referrals first."
                )
            )

    def on_trash(self):
        if self.docstatus != 0:
            frappe.throw(_("Only draft correspondence can be deleted."))

        for doctype in ("Murasalat Referral", "Murasalat Correspondence Document"):
            if frappe.db.exists(doctype, {"correspondence": self.name}):
                frappe.throw(
                    _("The correspondence cannot be deleted because linked {0} records exist.").format(
                        doctype
                    )
                )

    def set_defaults(self):
        profile = get_current_user_profile()

        if profile:
            self.company = self.company or profile.default_company
            self.owner_department = self.owner_department or profile.default_department

            if self.direction == "Internal":
                self.prepared_by = self.prepared_by or frappe.session.user
                self.prepared_by_employee = self.prepared_by_employee or profile.employee

        settings = frappe.get_cached_doc("Murasalat Settings")
        self.company = self.company or settings.company
        self.owner_department = self.owner_department or settings.default_department
        self.confidentiality_level = self.confidentiality_level or settings.default_confidentiality
        self.priority_level = self.priority_level or settings.default_priority

    def set_direction_defaults(self):
        if self.direction == "Incoming":
            self.incoming_to_department = self.incoming_to_department or self.owner_department
        elif self.direction == "Internal":
            self.origin_department = self.origin_department or self.owner_department
        elif self.direction == "Outgoing":
            self.outgoing_from_department = self.outgoing_from_department or self.owner_department

    def set_hijri_dates(self):
        self.due_date_hijri = gregorian_to_hijri(self.due_date)
        self.external_letter_date_hijri = gregorian_to_hijri(self.external_letter_date)
        self.outgoing_letter_date_hijri = gregorian_to_hijri(self.outgoing_letter_date)

    def validate_direction(self):
        allowed = {"Internal", "Incoming", "Outgoing"}
        if self.direction not in allowed:
            frappe.throw(_("Invalid correspondence direction."))

    def validate_correspondence_type(self):
        type_data = frappe.db.get_value(
            "Murasalat Correspondence Type",
            self.correspondence_type,
            [
                "allow_internal",
                "allow_incoming",
                "allow_outgoing",
                "requires_letter_number",
                "requires_letter_date",
                "is_active",
            ],
            as_dict=True,
        )
        if not type_data or not type_data.is_active:
            frappe.throw(_("The selected correspondence type is inactive or does not exist."))

        allowed_by_direction = {
            "Internal": type_data.allow_internal,
            "Incoming": type_data.allow_incoming,
            "Outgoing": type_data.allow_outgoing,
        }
        if not allowed_by_direction.get(self.direction):
            frappe.throw(
                _("The selected correspondence type is not allowed for direction {0}.").format(
                    _(self.direction)
                )
            )

        if type_data.requires_letter_number:
            fieldname = (
                "external_letter_number"
                if self.direction == "Incoming"
                else "outgoing_letter_number"
                if self.direction == "Outgoing"
                else None
            )
            if fieldname and not self.get(fieldname):
                frappe.throw(_("A letter number is required for the selected correspondence type."))

        if type_data.requires_letter_date:
            fieldname = (
                "external_letter_date"
                if self.direction == "Incoming"
                else "outgoing_letter_date"
                if self.direction == "Outgoing"
                else None
            )
            if fieldname and not self.get(fieldname):
                frappe.throw(_("A letter date is required for the selected correspondence type."))

    def validate_active_link_values(self):
        checks = [
            ("Murasalat Confidentiality Level", self.confidentiality_level),
            ("Murasalat Priority Level", self.priority_level),
        ]
        if self.direction == "Incoming":
            checks.append(("Murasalat External Party", self.external_from_party))
        elif self.direction == "Outgoing":
            checks.append(("Murasalat External Party", self.external_to_party))

        for doctype, name in checks:
            if name and not frappe.db.get_value(doctype, name, "is_active"):
                frappe.throw(_("{0} {1} is inactive.").format(doctype, name))

    def validate_due_date(self):
        if self.due_date and getdate(self.due_date) < getdate(today()) and self.docstatus == 0:
            frappe.throw(_("Due Date cannot be earlier than today."))

    def validate_correspondence_links(self):
        seen = set()
        primary_count = 0

        for row in self.get("correspondence_links") or []:
            if row.linked_correspondence == self.name:
                frappe.throw(_("A correspondence cannot be linked to itself."))

            if row.linked_correspondence in seen:
                frappe.throw(
                    _("Duplicate linked correspondence: {0}").format(row.linked_correspondence)
                )
            seen.add(row.linked_correspondence)

            if row.is_primary_reference:
                primary_count += 1

        if primary_count > 1:
            frappe.throw(_("Only one linked correspondence can be the primary reference."))

        links = self.get("correspondence_links") or []
        if links and primary_count == 0:
            links[0].is_primary_reference = 1

    def validate_registration_requirements(self):
        requires_main_document = frappe.db.get_value(
            "Murasalat Correspondence Type",
            self.correspondence_type,
            "requires_main_document",
        )
        if requires_main_document and not frappe.db.exists(
            "Murasalat Correspondence Document",
            {"correspondence": self.name, "is_main_document": 1},
        ):
            frappe.throw(_("A main correspondence document is required before registration."))

    def validate_closed_state(self):
        previous_state = self._doc_before_save.workflow_state if self._doc_before_save else None

        if previous_state == CLOSED_STATE and self.workflow_state != CLOSED_STATE:
            self.closed_by = None
            self.closed_on = None

        if self.workflow_state != CLOSED_STATE or self.is_new():
            return

        open_referrals = frappe.db.count(
            "Murasalat Referral",
            {
                "correspondence": self.name,
                "workflow_state": ["in", list(ACTIVE_REFERRAL_STATES)],
                "action_required": 1,
            },
        )
        if open_referrals:
            frappe.throw(
                _(
                    "The correspondence cannot be closed while action-required referrals are active."
                )
            )

        if not self.closed_by:
            self.closed_by = frappe.session.user
        if not self.closed_on:
            self.closed_on = now()

    def issue_correspondence_number(self):
        if self.correspondence_number:
            return

        rule = get_numbering_rule(self.direction, self.correspondence_type)
        if not rule:
            frappe.throw(
                _("No active numbering rule was found for direction {0}.").format(
                    _(self.direction)
                )
            )

        digits = max(cint(rule.digits), 1)
        year = None
        if rule.include_year:
            year = (
                str(get_hijri_year(today()))
                if rule.year_type == "Hijri"
                else str(getdate(today()).year)
            )

        series_key = f"Murasalat/{rule.name}/{year or 'all'}/"
        sequence = getseries(series_key, digits)
        prefix = (rule.prefix or "").strip().rstrip("-./")

        parts = [prefix]
        if year:
            parts.append(year)
        parts.append(str(sequence).zfill(digits))
        self.correspondence_number = "-".join(parts)


def get_current_user_profile(user: str | None = None):
    user = user or frappe.session.user
    profile_name = frappe.db.get_value(
        "Murasalat User Profile",
        {"user": user, "is_active": 1},
        "name",
    )
    return frappe.get_cached_doc("Murasalat User Profile", profile_name) if profile_name else None


def get_numbering_rule(direction: str, correspondence_type: str):
    fields = ["name", "prefix", "digits", "include_year", "year_type"]

    specific = frappe.get_all(
        "Murasalat Numbering Rule",
        {
            "direction": direction,
            "correspondence_type": correspondence_type,
            "is_active": 1,
        },
        fields,
        order_by="modified desc",
        limit=1,
    )
    if specific:
        return frappe._dict(specific[0])

    default = frappe.get_all(
        "Murasalat Numbering Rule",
        {
            "direction": direction,
            "is_default": 1,
            "is_active": 1,
        },
        fields,
        order_by="modified desc",
        limit=1,
    )
    return frappe._dict(default[0]) if default else None
