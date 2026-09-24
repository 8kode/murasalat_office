"""Idempotent master-data bootstrap for a fresh site.

Seeds *data* only: the lookup tables the transaction DocTypes link to. It never
creates a role, a permission row, a workflow or a workflow state — those are site
configuration under the application's Native-First principle.

Included because a first save fails without them, exactly as written in the field
defaults on Murasalat Correspondence:

============================ ========================================== =============
Correspondence field         links to                                   default value
============================ ========================================== =============
``transaction_type``         Murasalat Transaction Type                 ``مذكرة``
``confidentiality``          Murasalat Confidentiality Level            ``عام``
``importance``               Murasalat Importance Level                 ``متوسط``
``correspondence_direction`` Murasalat Correspondence Direction         ``Internal``
attachments.``type``         Murasalat Attachment Type                  ``Attachment``
============================ ========================================== =============

``Murasalat Correspondence Direction`` must contain ``Incoming``, ``Outgoing`` and
``Internal`` by those exact names: ``services.lifecycle.register_correspondence``
resolves the initial holder from a dict keyed on those three strings, so a renamed
direction makes registration throw.

Usage:

    bench --site <site> execute murasalat_office.setup.master_data.seed

Safe to re-run: each record is created only when it is missing, and the call returns
what it created, what already existed, and anything a launch still needs (``verify``).

The seeded titles are a reviewable starting set, not a business decision — rename or
extend them in Desk at any time.
"""

import frappe

TRANSACTION_TYPES = [
    {"title": "مذكرة"},
    {"title": "خطاب"},
    {"title": "تعميم"},
    {"title": "قرار"},
    {"title": "محضر"},
]

CONFIDENTIALITY_LEVELS = [
    {"title": "عام", "clearance_rank": 0, "color": "#2f9e63"},
    {"title": "مقيّد", "clearance_rank": 1, "color": "#c9821f"},
    {"title": "سري", "clearance_rank": 2, "color": "#b03a2e"},
    {"title": "سري للغاية", "clearance_rank": 3, "color": "#6b1f18"},
]

IMPORTANCE_LEVELS = [
    {"title": "عادي", "color": "#5c7570"},
    {"title": "متوسط", "color": "#c9821f"},
    {"title": "عاجل", "color": "#b03a2e"},
]

CORRESPONDENCE_DIRECTIONS = [
    {"correspondence_direction": "Incoming", "arabic_label": "وارد"},
    {"correspondence_direction": "Outgoing", "arabic_label": "صادر"},
    {"correspondence_direction": "Internal", "arabic_label": "داخلي"},
]

REFERRAL_DIRECTIONS = [
    {"title": "Incoming"},
    {"title": "Outgoing"},
    {"title": "Internal"},
]

EXTERNAL_PARTY_TYPES = [
    {"type": "جهة حكومية"},
    {"type": "شركة"},
    {"type": "فرد"},
]

ATTACHMENT_TYPES = [
    {"attachment_type": "Main Letter", "type_label": "الخطاب الأصلي",
     "description": "الخطاب نفسه الذي تحمله المعاملة أو الإحالة."},
    {"attachment_type": "Attachment", "type_label": "مرفق مساند",
     "description": "أي ورقة تصاحب الخطاب: كشف، جدول، نموذج، صورة."},
    {"attachment_type": "Reply", "type_label": "الرد",
     "description": "الرد الوارد على الخطاب."},
    {"attachment_type": "Copy for Information", "type_label": "صورة للعلم",
     "description": "نسخة تُرسل للعلم لا للإجراء."},
    {"attachment_type": "Translation", "type_label": "ترجمة",
     "description": "ترجمة الخطاب أو مرفقه."},
]

# Where the paper original is filed. Four places cover a small correspondence office; the
# list is reference data, so a site adds its own in Desk whenever its archive differs.
ARCHIVE_LOCATIONS = [
    {"location": "Correspondence Office", "location_label": "مكتب المراسلات",
     "description": "الملف الجاري لدى مكتب المراسلات."},
    {"location": "Central Archive", "location_label": "الأرشيف المركزي",
     "description": "الملفات المنتهية المحفوظة في الأرشيف."},
    {"location": "Department Shelf", "location_label": "رف القسم",
     "description": "ورق محفوظ لدى القسم المعني."},
    {"location": "Director Office", "location_label": "مكتب المدير",
     "description": "ملفات محفوظة لدى مكتب المدير."},
]

# doctype -> (name field, records)
MASTER_DATA = [
    ("Murasalat Transaction Type", "title", TRANSACTION_TYPES),
    ("Murasalat Confidentiality Level", "title", CONFIDENTIALITY_LEVELS),
    ("Murasalat Importance Level", "title", IMPORTANCE_LEVELS),
    ("Murasalat Correspondence Direction", "correspondence_direction", CORRESPONDENCE_DIRECTIONS),
    ("Murasalat Referral Direction", "title", REFERRAL_DIRECTIONS),
    ("Murasalat External Party Type", "type", EXTERNAL_PARTY_TYPES),
    ("Murasalat Attachment Type", "attachment_type", ATTACHMENT_TYPES),
    ("Murasalat Archive Location", "location", ARCHIVE_LOCATIONS),
]

# The lookup values the DocType field defaults point at. A first save needs these.
REQUIRED_BY_DEFAULTS = [
    ("Murasalat Transaction Type", "مذكرة"),
    ("Murasalat Confidentiality Level", "عام"),
    ("Murasalat Importance Level", "متوسط"),
    ("Murasalat Correspondence Direction", "Internal"),
    ("Murasalat Correspondence Direction", "Incoming"),
    ("Murasalat Correspondence Direction", "Outgoing"),
    ("Murasalat Attachment Type", "Attachment"),
]


def _insert(doctype, record, dry_run):
    """Create one record unless it already exists. Returns 'exists' or 'created'."""
    key_field = _NAME_FIELD[doctype]
    name = record[key_field]

    if frappe.db.exists(doctype, name):
        return "exists"

    if dry_run:
        return "planned"

    values = {"doctype": doctype}
    values.update(record)

    # An explicit administrator bootstrap: the caller is expected to be a System
    # Manager running bench execute, not a regular user going around permissions.
    frappe.get_doc(values).insert(ignore_permissions=True)

    return "created"


_NAME_FIELD = {doctype: field for doctype, field, _ in MASTER_DATA}


def seed(dry_run=False):
    """Seed every master-data table. Idempotent; returns a per-record report."""
    report = {"created": [], "exists": [], "planned": []}

    for doctype, key_field, records in MASTER_DATA:
        for record in records:
            outcome = _insert(doctype, record, dry_run)
            report[outcome].append({"doctype": doctype, "name": record[key_field]})

    report.update(
        {
            "dry_run": bool(dry_run),
            "missing_required": verify(),
        }
    )

    return report


def verify():
    """Return the launch-critical lookup values that are still missing.

    Empty list means the correspondence defaults resolve and every direction the
    registration method switches on exists.
    """
    missing = []

    for doctype, name in REQUIRED_BY_DEFAULTS:
        try:
            if not frappe.db.exists(doctype, name):
                missing.append({"doctype": doctype, "name": name})
        except Exception:  # noqa: BLE001 — a half-installed site must not crash the report
            missing.append({"doctype": doctype, "name": name, "error": "unavailable"})

    return missing
