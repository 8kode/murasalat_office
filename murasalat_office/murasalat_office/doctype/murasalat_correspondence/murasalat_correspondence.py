import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime, getdate

from murasalat_office.services.records import seal, validate_immutable_fields, verify_integrity

REFERRAL_OPEN_STATES = {"Pending", "Sent", "Received", "In Progress", "Overdue"}
REFERRAL_CLOSED_STATES = {"Completed", "Rejected", "Returned", "Withdrawn", "Cancelled"}
TERMINAL_STATUSES = {"Closed", "Withdrawn", "Rejected"}


class MurasalatCorrespondence(Document):
    def validate(self):
        validate_immutable_fields(self)
        if not self.originating_organization:
            self.originating_organization = self.source_entity or self.target_entity
        self._validate_links()
        self._validate_referrals()
        self._apply_operational_timestamps()
        self._mark_overdue_referrals()
        self._sync_current_holder()
        self._validate_lifecycle()

    def _validate_lifecycle(self):
        if self.status in TERMINAL_STATUSES and self.referrals:
            if any(r.status in REFERRAL_OPEN_STATES for r in self.referrals):
                frappe.throw("Cannot close a correspondence while referrals are still open.")

    def _validate_links(self):
        seen = set()
        for row in self.links or []:
            if row.linked_correspondence == self.name:
                frappe.throw("A correspondence cannot link to itself.")
            key = (row.linked_correspondence, row.relationship_type)
            if key in seen:
                frappe.throw("Duplicate correspondence link detected.")
            seen.add(key)

    def _validate_referrals(self):
        seen = set()
        for row in self.referrals or []:
            recipient = row.recipient_user or row.recipient_organization
            if not recipient:
                frappe.throw("Each referral must have either a recipient user or organization.")
            key = (row.recipient_type, recipient, row.direction)
            if key in seen:
                frappe.throw("Duplicate recipient and direction detected in the same referral set.")
            seen.add(key)

    def _apply_operational_timestamps(self):
        for index, row in enumerate(self.referrals or [], start=1):
            if not row.referral_number:
                row.referral_number = f"{self.name or 'NEW'}-R{index:03d}"
            if row.status == "Sent" and not row.sent_on:
                row.sent_on = now_datetime()
            if row.status in {"Received", "In Progress", "Completed"} and not row.received_on:
                row.received_on = now_datetime(); row.received_by = frappe.session.user
            if row.status == "Completed" and not row.completed_on:
                row.completed_on = now_datetime(); row.completed_by = frappe.session.user

    def _mark_overdue_referrals(self):
        today = getdate()
        for row in self.referrals or []:
            if row.status in REFERRAL_OPEN_STATES and row.due_date and getdate(row.due_date) < today:
                row.status = "Overdue"

    def _sync_current_holder(self):
        open_rows = [r for r in self.referrals or [] if r.status in REFERRAL_OPEN_STATES]
        if not open_rows:
            self.current_holder = None; self.current_holder_user = None; return
        row = open_rows[-1]
        self.current_holder = row.recipient_organization if row.recipient_type == "Organization" else None
        self.current_holder_user = row.recipient_user if row.recipient_type == "User" else None

    def before_save(self):
        old = self.get_doc_before_save()
        if self.status == "Registered" and (not old or old.status != "Registered"):
            if not self.registered_on:
                self.registered_on = now_datetime()
            seal(self, "Registered")

    def after_insert(self):
        self._append_activity("Created", details="Correspondence created.")
        self._sync_referral_todos()
        self._secure_secret_attachments()

    def _secure_secret_attachments(self):
        """Protect secret/classified attachments and ensure their hashes are stored.

        The child table is the canonical metadata layer. Frappe's File document
        remains the canonical file record. We do not duplicate file content.
        """
        classified_values = {
            "Secret", "Confidential", "Top Secret",
            "سري", "سري للغاية", "محدود",
        }
        classified = (self.confidentiality or "").strip() in classified_values

        for row in self.attachments or []:
            if not row.file:
                continue

            # A classified correspondence makes every attached file restricted.
            if classified:
                row.is_secret = 1

            if not row.file_hash:
                file_name = frappe.db.get_value("File", {"file_url": row.file}, "name")
                if file_name:
                    file_doc = frappe.get_doc("File", file_name)
                    try:
                        content = file_doc.get_content()
                    except Exception:
                        content = None
                    if content is not None:
                        import hashlib
                        if isinstance(content, str):
                            content = content.encode()
                        row.file_hash = hashlib.sha256(content).hexdigest()

            if row.is_secret:
                file_name = frappe.db.get_value("File", {"file_url": row.file}, "name")
                if file_name:
                    file_doc = frappe.get_doc("File", file_name)
                    if not file_doc.is_private:
                        file_doc.is_private = 1
                        file_doc.save(ignore_permissions=True)

            # after_insert runs after child rows are already inserted, so persist
            # metadata explicitly instead of relying on a later parent save.
            if row.name and not str(row.name).startswith("new-"):
                frappe.db.set_value(
                    row.doctype, row.name,
                    {"is_secret": int(bool(row.is_secret)), "file_hash": row.file_hash},
                    update_modified=False,
                )

    def on_update(self):
        old = self.get_doc_before_save()
        if self.status == "Closed" and not self.closed_on:
            self.closed_on = now_datetime()
        if old and old.status != "Reopened" and self.status == "Reopened":
            self.reopened_on = now_datetime(); self.reopened_by = frappe.session.user
            self._append_activity("Reopened", details="Correspondence reopened; historical record retained.")
        if self.status == "Registered" and self.integrity_hash and not verify_integrity(self):
            frappe.throw("Integrity verification failed. Registered record content differs from its sealed snapshot.")
        self._sync_referral_todos(); self._sync_activity_log()

    def _append_activity(self, activity_type, referral=None, details=None):
        self.append("activities", {"activity_type": activity_type, "activity_on": now_datetime(), "actor": frappe.session.user,
            "organization": getattr(referral, "recipient_organization", None) if referral else self.current_holder,
            "referral_number": getattr(referral, "referral_number", None) if referral else None, "details": details})

    def _sync_activity_log(self):
        existing = {(r.activity_type, r.referral_number) for r in self.activities or []}
        mapping = {"Sent":"Referral Sent","Received":"Referral Received","In Progress":"Referral Received","Completed":"Referral Completed","Rejected":"Referral Rejected","Cancelled":"Referral Closed","Withdrawn":"Referral Closed","Returned":"Referral Closed"}
        for row in self.referrals or []:
            activity_type = mapping.get(row.status); key = (activity_type, row.referral_number)
            if activity_type and key not in existing:
                self._append_activity(activity_type, referral=row, details=f"Referral status: {row.status}"); existing.add(key)

    def _sync_referral_todos(self):
        changed = False
        for row in self.referrals or []:
            if row.recipient_type != "User" or not row.recipient_user: continue
            if row.status in REFERRAL_OPEN_STATES and not row.referral_todo:
                todo = frappe.get_doc({"doctype":"ToDo","allocated_to":row.recipient_user,"reference_type":self.doctype,"reference_name":self.name,"description":self.subject,"priority":self._todo_priority(row.importance),"date":row.due_date,"status":"Open","assigned_by":frappe.session.user}).insert(ignore_permissions=True)
                row.referral_todo = todo.name; changed = True
            elif row.referral_todo and row.status in REFERRAL_CLOSED_STATES and frappe.db.exists("ToDo", row.referral_todo):
                frappe.db.set_value("ToDo", row.referral_todo, "status", "Cancelled", update_modified=False)
        if changed and not self.is_new(): self.flags.referral_todos_synced = True

    @staticmethod
    def _todo_priority(importance):
        value = (importance or "").lower()
        if any(t in value for t in ("critical", "very urgent", "حالًا", "عاجل جدًا")): return "High"
        if any(t in value for t in ("urgent", "عاجل")): return "Medium"
        return "Low"
