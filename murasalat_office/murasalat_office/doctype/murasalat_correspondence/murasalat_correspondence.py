from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.naming import make_autoname
from frappe.utils import cint, getdate, now, now_datetime, today

from murasalat_office.utils.dates import gregorian_to_hijri


ACTIVE_REFERRAL_STATUSES = ("Sent", "Received", "In Progress")
COMPLETED_REFERRAL_STATUSES = ("Completed",)
INACTIVE_REFERRAL_STATUSES = ("Returned", "Withdrawn", "Cancelled")

REGISTERED_STATE = "Murasalat Registered"
CLOSED_STATE = "Murasalat Closed"
DRAFT_STATE = "Murasalat Draft"


class MurasalatCorrespondence(Document):
    def before_validate(self):
        self.set_defaults()
        self.set_hijri_dates()
        self.set_identification_values()
        self.set_direction_specific_defaults()

    def autoname(self):
        self.name = self.generate_correspondence_number()

    def validate(self):
        self.validate_direction()
        self.validate_correspondence_type()
        self.validate_page_count()
        self.validate_due_date()
        self.validate_correspondence_links()
        self.validate_closed_state()

    def before_submit(self):
        self.validate_registration_requirements()

        if not self.registered_by:
            self.registered_by = frappe.session.user

        if not self.registered_on:
            self.registered_on = now()

        self.workflow_state = self.workflow_state or REGISTERED_STATE

    def on_submit(self):
        self.db_set("barcode", self.correspondence_number, update_modified=False)
        self.db_set("qr_code", self.correspondence_number, update_modified=False)

    def before_cancel(self):
        open_referrals = frappe.db.count(
            "Murasalat Referral",
            filters={
                "correspondence": self.name,
                "status": ["in", list(ACTIVE_REFERRAL_STATUSES)],
            },
        )

        if open_referrals:
            frappe.throw(
                _(
                    "The correspondence cannot be cancelled while it has active referrals. "
                    "Withdraw or cancel the active referrals first."
                )
            )

    def on_cancel(self):
        self.db_set("last_activity_on", now(), update_modified=False)

    def on_trash(self):
        if self.docstatus != 0:
            frappe.throw(_("Only draft correspondence can be deleted."))

        if frappe.db.exists(
            "Murasalat Referral",
            {"correspondence": self.name},
        ):
            frappe.throw(
                _("The correspondence cannot be deleted because referrals exist.")
            )

        if frappe.db.exists(
            "Murasalat Correspondence Document",
            {"correspondence": self.name},
        ):
            frappe.throw(
                _("The correspondence cannot be deleted because documents exist.")
            )

    def set_defaults(self):
        profile = get_current_user_profile()

        if profile:
            self.company = self.company or profile.get("default_company")
            self.owner_department = (
                self.owner_department or profile.get("default_department")
            )

            if self.direction == "Internal":
                self.origin_department = (
                    self.origin_department or profile.get("default_department")
                )
                self.prepared_by_employee = (
                    self.prepared_by_employee or profile.get("employee")
                )

            if self.direction == "Outgoing":
                self.outgoing_from_department = (
                    self.outgoing_from_department
                    or profile.get("default_department")
                )

        if frappe.db.exists("DocType", "Murasalat Settings"):
            settings = frappe.get_cached_doc("Murasalat Settings")

            self.company = self.company or settings.company
            self.owner_department = (
                self.owner_department or settings.default_department
            )
            self.confidentiality_level = (
                self.confidentiality_level
                or settings.default_confidentiality
            )
            self.priority_level = self.priority_level or settings.default_priority

        if not self.prepared_by and self.direction == "Internal":
            self.prepared_by = frappe.session.user

    def set_direction_specific_defaults(self):
        if self.direction == "Incoming":
            self.incoming_to_department = (
                self.incoming_to_department or self.owner_department
            )

        if self.direction == "Internal":
            self.origin_department = (
                self.origin_department or self.owner_department
            )

        if self.direction == "Outgoing":
            self.outgoing_from_department = (
                self.outgoing_from_department or self.owner_department
            )

    def set_hijri_dates(self):
        self.due_date_hijri = gregorian_to_hijri(self.due_date)
        self.external_letter_date_hijri = gregorian_to_hijri(
            self.external_letter_date
        )
        self.outgoing_letter_date_hijri = gregorian_to_hijri(
            self.outgoing_letter_date
        )

    def set_identification_values(self):
        if self.name and not self.is_new():
            self.correspondence_number = (
                self.correspondence_number or self.name
            )
            self.barcode = self.correspondence_number
            self.qr_code = self.correspondence_number

    def validate_direction(self):
        allowed = ("Internal", "Incoming", "Outgoing")

        if self.direction not in allowed:
            frappe.throw(_("Invalid correspondence direction."))

        if self.direction == "Internal":
            if not self.origin_department:
                frappe.throw(_("Origin Department is required."))

            self.external_from_party = None
            self.incoming_to_department = None
            self.external_letter_number = None
            self.external_letter_date = None
            self.external_letter_date_hijri = None

            self.outgoing_from_department = None
            self.external_to_party = None
            self.outgoing_letter_number = None
            self.outgoing_letter_date = None
            self.outgoing_letter_date_hijri = None

        elif self.direction == "Incoming":
            if not self.external_from_party:
                frappe.throw(_("External Sender is required."))

            if not self.incoming_to_department:
                frappe.throw(_("Internal Recipient Department is required."))

            self.origin_department = None
            self.outgoing_from_department = None
            self.external_to_party = None
            self.outgoing_letter_number = None
            self.outgoing_letter_date = None
            self.outgoing_letter_date_hijri = None

        elif self.direction == "Outgoing":
            if not self.outgoing_from_department:
                frappe.throw(_("Sending Department is required."))

            if not self.external_to_party:
                frappe.throw(_("External Recipient is required."))

            self.origin_department = None
            self.external_from_party = None
            self.incoming_to_department = None
            self.external_letter_number = None
            self.external_letter_date = None
            self.external_letter_date_hijri = None

    def validate_correspondence_type(self):
        if not self.correspondence_type:
            return

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

        if not type_data:
            frappe.throw(_("The selected correspondence type does not exist."))

        if not type_data.is_active:
            frappe.throw(_("The selected correspondence type is inactive."))

        direction_permission = {
            "Internal": type_data.allow_internal,
            "Incoming": type_data.allow_incoming,
            "Outgoing": type_data.allow_outgoing,
        }

        if not direction_permission.get(self.direction):
            frappe.throw(
                _(
                    "The selected correspondence type is not allowed for direction {0}."
                ).format(_(self.direction))
            )

        if type_data.requires_letter_number:
            if self.direction == "Incoming" and not self.external_letter_number:
                frappe.throw(_("External Letter Number is required."))

            if self.direction == "Outgoing" and not self.outgoing_letter_number:
                frappe.throw(_("Outgoing Letter Number is required."))

        if type_data.requires_letter_date:
            if self.direction == "Incoming" and not self.external_letter_date:
                frappe.throw(_("External Letter Date is required."))

            if self.direction == "Outgoing" and not self.outgoing_letter_date:
                frappe.throw(_("Outgoing Letter Date is required."))

    def validate_page_count(self):
        if self.page_count is not None and cint(self.page_count) < 0:
            frappe.throw(_("Page Count cannot be negative."))

    def validate_due_date(self):
        if self.due_date and getdate(self.due_date) < getdate(today()):
            if self.is_new() or self.docstatus == 0:
                frappe.throw(_("Due Date cannot be earlier than today."))

    def validate_correspondence_links(self):
        links = self.get("correspondence_links") or []

        if not self.link_to_other_correspondence:
            if links:
                frappe.throw(
                    _(
                        "Enable Link to Other Correspondence before adding correspondence links."
                    )
                )
            return

        seen = set()
        primary_rows = []

        for row in links:
            if not row.linked_correspondence:
                continue

            if row.linked_correspondence == self.name:
                frappe.throw(
                    _("A correspondence cannot be linked to itself.")
                )

            if row.linked_correspondence in seen:
                frappe.throw(
                    _("Duplicate linked correspondence: {0}").format(
                        row.linked_correspondence
                    )
                )

            seen.add(row.linked_correspondence)

            if row.is_primary_reference:
                primary_rows.append(row)

        if len(primary_rows) > 1:
            frappe.throw(
                _("Only one linked correspondence can be the primary reference.")
            )

        if links and not primary_rows:
            links[0].is_primary_reference = 1

    def validate_registration_requirements(self):
        if not self.subject:
            frappe.throw(_("Subject is required."))

        if not self.correspondence_type:
            frappe.throw(_("Correspondence Type is required."))

        if not self.confidentiality_level:
            frappe.throw(_("Confidentiality Level is required."))

        if not self.priority_level:
            frappe.throw(_("Priority Level is required."))

        requires_main_document = frappe.db.get_value(
            "Murasalat Correspondence Type",
            self.correspondence_type,
            "requires_main_document",
        )

        if requires_main_document:
            main_document_exists = frappe.db.exists(
                "Murasalat Correspondence Document",
                {
                    "correspondence": self.name,
                    "is_main_document": 1,
                },
            )

            if not main_document_exists:
                frappe.throw(
                    _("A main correspondence document is required before registration.")
                )

    def validate_closed_state(self):
        if self.workflow_state != CLOSED_STATE:
            return

        open_referrals = frappe.db.count(
            "Murasalat Referral",
            filters={
                "correspondence": self.name,
                "status": ["in", list(ACTIVE_REFERRAL_STATUSES)],
                "action_required": 1,
            },
        )

        if open_referrals:
            frappe.throw(
                _(
                    "The correspondence cannot be closed while action-required referrals are active."
                )
            )

    def generate_correspondence_number(self) -> str:
        rule = get_numbering_rule(
            direction=self.direction,
            correspondence_type=self.correspondence_type,
        )

        if not rule:
            frappe.throw(
                _("No active numbering rule was found for direction {0}.").format(
                    _(self.direction)
                )
            )

        prefix = (rule.prefix or "").strip().rstrip("-./")
        digits = max(cint(rule.digits), 1)

        if rule.include_year:
            if rule.year_type == "Hijri":
                hijri_date = gregorian_to_hijri(today())
                if not hijri_date:
                    frappe.throw(_("Unable to calculate the Hijri year."))
                year = hijri_date.split("-")[0]
            else:
                year = str(getdate(today()).year)

            series = f"{prefix}-{year}-.{'#' * digits}"
        else:
            series = f"{prefix}-.{'#' * digits}"

        generated_name = make_autoname(
            series,
            doctype=self.doctype,
            doc=self,
        )

        self.correspondence_number = generated_name
        self.barcode = generated_name
        self.qr_code = generated_name

        return generated_name

    @frappe.whitelist()
    def create_multiple_referrals(self, referrals):
        self.check_permission("read")

        if self.is_new():
            frappe.throw(_("Save the correspondence before creating referrals."))

        if self.docstatus != 1:
            frappe.throw(
                _("The correspondence must be registered before referrals can be sent.")
            )

        if self.workflow_state == CLOSED_STATE:
            frappe.throw(_("Closed correspondence cannot be referred."))

        if not frappe.has_permission("Murasalat Referral", ptype="create"):
            frappe.throw(_("You are not permitted to create referrals."), frappe.PermissionError)

        rows = frappe.parse_json(referrals)

        if not isinstance(rows, list) or not rows:
            frappe.throw(_("Add at least one referral recipient."))

        profile = get_current_user_profile()

        if not profile or not profile.get("default_department"):
            frappe.throw(
                _("The current user does not have a default Murasalat department.")
            )

        batch_id = frappe.generate_hash(length=12)
        created_referrals = []
        duplicate_keys = set()

        frappe.db.savepoint("before_multiple_referrals")

        try:
            for index, row in enumerate(rows, start=1):
                row = frappe._dict(row)
                validate_referral_row(row, duplicate_keys)

                is_copy = cint(row.get("send_copy")) or cint(row.get("is_copy"))
                action_required = 0 if is_copy else 1

                referral = frappe.get_doc(
                    {
                        "doctype": "Murasalat Referral",
                        "correspondence": self.name,
                        "from_user": frappe.session.user,
                        "from_department": profile.default_department,
                        "recipient_type": row.recipient_type,
                        "to_user": (
                            row.to_user
                            if row.recipient_type == "User"
                            else None
                        ),
                        "to_department": (
                            row.to_department
                            if row.recipient_type == "Department"
                            else None
                        ),
                        "routing_purpose": row.routing_purpose,
                        "priority_level": (
                            row.priority_level or self.priority_level
                        ),
                        "due_date": row.due_date,
                        "instructions": row.instructions,
                        "is_private": cint(row.is_private),
                        "paper_correspondence": cint(
                            row.paper_correspondence
                        ),
                        "send_copy": is_copy,
                        "is_copy": is_copy,
                        "action_required": action_required,
                        "for_follow_up": cint(row.for_follow_up),
                        "referral_batch": batch_id,
                        "referral_sequence": index,
                        "status": "Sent",
                        "sent_on": now(),
                    }
                )

                referral.insert()
                created_referrals.append(referral.name)

        except Exception:
            frappe.db.rollback(save_point="before_multiple_referrals")
            raise

        update_correspondence_routing_summary(self.name)

        return {
            "batch_id": batch_id,
            "created_count": len(created_referrals),
            "referrals": created_referrals,
        }

    @frappe.whitelist()
    def get_form_dashboard_data(self):
        self.check_permission("read")

        if self.is_new():
            return {
                "documents": [],
                "referrals": [],
            }

        documents = frappe.get_list(
            "Murasalat Correspondence Document",
            filters={"correspondence": self.name},
            fields=[
                "name",
                "document_category",
                "document_type",
                "file_name",
                "file",
                "is_secret",
                "is_main_document",
                "uploaded_by",
                "uploaded_on",
            ],
            order_by="uploaded_on desc",
            limit_page_length=100,
        )

        referrals = frappe.get_list(
            "Murasalat Referral",
            filters={"correspondence": self.name},
            fields=[
                "name",
                "recipient_type",
                "to_user",
                "to_department",
                "routing_purpose",
                "priority_level",
                "due_date",
                "status",
                "is_copy",
                "for_follow_up",
                "sent_on",
                "completed_on",
            ],
            order_by="creation desc",
            limit_page_length=200,
        )

        return {
            "documents": documents,
            "referrals": referrals,
        }


def validate_referral_row(row: frappe._dict, duplicate_keys: set):
    if row.recipient_type not in ("User", "Department"):
        frappe.throw(_("Recipient Type must be User or Department."))

    if row.recipient_type == "User":
        if not row.to_user:
            frappe.throw(_("To User is required for user referrals."))

        if row.to_department:
            frappe.throw(
                _("To Department must be empty when Recipient Type is User.")
            )

        recipient_key = ("User", row.to_user)

    else:
        if not row.to_department:
            frappe.throw(
                _("To Department is required for department referrals.")
            )

        if row.to_user:
            frappe.throw(
                _("To User must be empty when Recipient Type is Department.")
            )

        recipient_key = ("Department", row.to_department)

    if recipient_key in duplicate_keys:
        frappe.throw(
            _("Duplicate referral recipient: {0}").format(
                recipient_key[1]
            )
        )

    duplicate_keys.add(recipient_key)

    if not row.routing_purpose:
        frappe.throw(_("Routing Purpose is required for every referral."))

    if row.due_date and getdate(row.due_date) < getdate(today()):
        frappe.throw(
            _("Referral Due Date cannot be earlier than today.")
        )


def get_current_user_profile(user: str | None = None):
    user = user or frappe.session.user

    if not frappe.db.exists("DocType", "Murasalat User Profile"):
        return None

    profile_name = frappe.db.get_value(
        "Murasalat User Profile",
        {
            "user": user,
            "is_active": 1,
        },
        "name",
    )

    if not profile_name:
        return None

    return frappe.get_cached_doc(
        "Murasalat User Profile",
        profile_name,
    )


def get_numbering_rule(direction: str, correspondence_type: str | None = None):
    fields = [
        "name",
        "prefix",
        "digits",
        "include_year",
        "year_type",
    ]

    if correspondence_type:
        rules = frappe.get_all(
            "Murasalat Numbering Rule",
            filters={
                "direction": direction,
                "correspondence_type": correspondence_type,
                "is_active": 1,
            },
            fields=fields,
            order_by="is_default desc, modified desc",
            limit=1,
        )

        if rules:
            return frappe._dict(rules[0])

    rules = frappe.get_all(
        "Murasalat Numbering Rule",
        filters={
            "direction": direction,
            "is_default": 1,
            "is_active": 1,
        },
        or_filters={
            "correspondence_type": ["is", "not set"],
            "correspondence_type": "",
        },
        fields=fields,
        order_by="modified desc",
        limit=1,
    )

    if not rules:
        rules = frappe.get_all(
            "Murasalat Numbering Rule",
            filters={
                "direction": direction,
                "is_default": 1,
                "is_active": 1,
            },
            fields=fields,
            order_by="modified desc",
            limit=1,
        )

    return frappe._dict(rules[0]) if rules else None


def update_correspondence_routing_summary(correspondence: str):
    if not correspondence or not frappe.db.exists(
        "Murasalat Correspondence",
        correspondence,
    ):
        return

    rows = frappe.get_all(
        "Murasalat Referral",
        filters={"correspondence": correspondence},
        fields=["status", "due_date", "sent_on", "modified"],
    )

    total_count = len(rows)
    active_count = 0
    completed_count = 0
    overdue_count = 0
    last_referred_on = None
    last_activity_on = None
    current_date = getdate(today())

    for row in rows:
        if row.status in ACTIVE_REFERRAL_STATUSES:
            active_count += 1

            if row.due_date and getdate(row.due_date) < current_date:
                overdue_count += 1

        if row.status in COMPLETED_REFERRAL_STATUSES:
            completed_count += 1

        if row.sent_on and (
            not last_referred_on or row.sent_on > last_referred_on
        ):
            last_referred_on = row.sent_on

        if row.modified and (
            not last_activity_on or row.modified > last_activity_on
        ):
            last_activity_on = row.modified

    pending_count = active_count

    if total_count == 0:
        routing_status = "No Referrals"
    elif overdue_count > 0:
        routing_status = "Overdue"
    elif active_count > 0 and completed_count > 0:
        routing_status = "Partially Completed"
    elif active_count > 0:
        routing_status = "Active"
    elif completed_count == total_count:
        routing_status = "Completed"
    else:
        routing_status = "Inactive"

    frappe.db.set_value(
        "Murasalat Correspondence",
        correspondence,
        {
            "routing_status": routing_status,
            "active_referral_count": active_count,
            "pending_referral_count": pending_count,
            "completed_referral_count": completed_count,
            "overdue_referral_count": overdue_count,
            "last_referred_on": last_referred_on,
            "last_activity_on": last_activity_on or now_datetime(),
        },
        update_modified=False,
    )