"""Read-only, permission-aware overview data for the Desk forms.

Design notes (why it is built this way):

* **Presentation only.** This module never decides access. It reads through
  ``frappe.get_list(..., ignore_permissions=False)`` and calls
  ``check_permission("read")`` on the anchor document, exactly like the reports do.
* **Server-rendered HTML.** Both panels are rendered here with Jinja2 and returned as
  one HTML string, so the client script stays a thin connector and the panel can be
  asserted on in tests. Autoescaping is on: a subject or an instruction block written by
  a user must never become markup.
* **Pure counters.** ``referral_kpis`` takes plain rows and a ``date`` and uses the
  standard library only, so the arithmetic is unit-testable without a Frappe runtime.
"""

from __future__ import annotations

import os
from collections.abc import Iterable
from datetime import date
from typing import Any

import frappe
from jinja2 import Environment, FileSystemLoader, select_autoescape

TEMPLATE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "templates",
    "overview",
)

ACTIVITY_AR = {
    "Created": "إنشاء",
    "Status Changed": "تغيير الحالة",
    "Registered": "تسجيل",
    "Closed": "إغلاق",
    "Sealed": "ختم",
    "Reopened": "إعادة فتح",
    "Referral Sent": "إرسال إحالة",
    "Referral Received": "استلام إحالة",
    "Referral Completed": "إكمال إحالة",
}

DIRECTION_AR = {"Incoming": "وارد", "Outgoing": "صادر", "Internal": "داخلي"}
RECIPIENT_TYPE_AR = {"User": "مستخدم", "Department": "قسم"}

REFERRAL_FIELDS = [
    "name",
    "referral_number",
    "correspondence",
    "recipient_type",
    "recipient_user",
    "recipient_department",
    "direction",
    "importance",
    "workflow_state",
    "due_date",
    "sent_on",
    "received_on",
    "completed_on",
    "received_by",
    "completed_by",
    "private_referral",
    "follow_up",
    "paper_copy",
    "cc_copy",
]

APPROVAL_FIELDS = [
    "name",
    "approval_level",
    "workflow_state",
    "requested_by",
    "requested_on",
    "approved_by",
    "approved_on",
    "decision_note",
]


def _as_date(value: Any) -> date | None:
    """Coerce a database value to a date without touching Frappe."""
    if not value:
        return None
    if isinstance(value, date):
        return value
    text = str(value).strip()
    if not text:
        return None
    return date.fromisoformat(text[:10])


def _days_left(due: Any, today_date: date) -> int | None:
    parsed = _as_date(due)
    if not parsed:
        return None
    return (parsed - today_date).days


def referral_kpis(rows: Iterable[dict], today_date: date) -> dict[str, int]:
    """Counters over referral rows that the caller already filtered by permission.

    A referral counts as a draft until it is sent, as completed once completed,
    and otherwise as open. Overdue and due-today are subsets of open.
    """
    kpis = {
        "total": 0,
        "draft": 0,
        "open": 0,
        "overdue": 0,
        "due_today": 0,
        "completed": 0,
    }

    for row in rows:
        kpis["total"] += 1

        if not row.get("sent_on"):
            kpis["draft"] += 1
            continue

        if row.get("completed_on"):
            kpis["completed"] += 1
            continue

        kpis["open"] += 1

        left = _days_left(row.get("due_date"), today_date)
        if left is None:
            continue
        if left < 0:
            kpis["overdue"] += 1
        elif left == 0:
            kpis["due_today"] += 1

    return kpis


def decorate_referrals(rows: Iterable[dict], today_date: date) -> list[dict]:
    """Add the presentation-only fields the template needs."""
    decorated = []

    for row in rows:
        item = dict(row)
        item["days_left"] = _days_left(row.get("due_date"), today_date)
        item["is_draft"] = not row.get("sent_on")
        item["is_completed"] = bool(row.get("completed_on"))
        item["is_open"] = bool(row.get("sent_on")) and not row.get("completed_on")
        item["is_overdue"] = bool(item["is_open"] and item["days_left"] is not None and item["days_left"] < 0)
        item["is_due_today"] = bool(item["is_open"] and item["days_left"] == 0)
        item["recipient_label"] = (
            row.get("recipient_user") or row.get("recipient_department") or "—"
        )
        item["recipient_type_ar"] = RECIPIENT_TYPE_AR.get(
            row.get("recipient_type"), row.get("recipient_type") or "—"
        )
        decorated.append(item)

    return decorated


def _activity_rows(doc, limit: int = 15, referral_numbers: set | None = None) -> list[dict]:
    """Newest-first activity rows, optionally scoped to one referral."""
    rows = []

    for row in reversed(list(doc.activities or [])):
        if referral_numbers is not None and row.referral_number not in referral_numbers:
            continue

        rows.append(
            {
                "activity_type": row.activity_type,
                "activity_type_ar": ACTIVITY_AR.get(row.activity_type, row.activity_type),
                "activity_on": row.activity_on,
                "actor": row.actor,
                "details": row.details,
                "referral_number": row.referral_number,
            }
        )

        if len(rows) >= limit:
            break

    return rows


def _environment() -> Environment:
    return Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=select_autoescape(["html"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )


def render(template_name: str, **context) -> str:
    return _environment().get_template(template_name).render(**context)


def _link_rows(doc) -> list[dict]:
    return [
        {
            "correspondence": row.linked_correspondence,
            "relationship": row.relationship_type,
            "remarks": row.get("remarks"),
        }
        for row in (doc.links or [])
        if row.linked_correspondence
    ]


def correspondence_overview(correspondence: str) -> dict:
    """Everything recorded against one correspondence, for a non-Administrator user."""
    doc = frappe.get_doc("Murasalat Correspondence", correspondence)
    doc.check_permission("read")

    today_date = frappe.utils.getdate(frappe.utils.today())

    referrals = frappe.get_list(
        "Murasalat Referral",
        filters={"correspondence": doc.name},
        fields=REFERRAL_FIELDS,
        ignore_permissions=False,
        limit_page_length=0,
        order_by="due_date asc, creation asc",
    )

    approvals = frappe.get_list(
        "Murasalat Approval Request",
        filters={"correspondence": doc.name},
        fields=APPROVAL_FIELDS,
        ignore_permissions=False,
        limit_page_length=0,
        order_by="approval_level asc, creation asc",
    )

    decorated = decorate_referrals(referrals, today_date)
    kpis = referral_kpis(referrals, today_date)

    attachments = list(doc.attachments or [])
    secret_count = sum(1 for row in attachments if row.is_secret)

    context = {
        "name": doc.name,
        "subject": doc.subject,
        "direction_ar": DIRECTION_AR.get(doc.correspondence_direction, doc.correspondence_direction),
        "direction": doc.correspondence_direction,
        "confidentiality": doc.confidentiality,
        "importance": doc.importance,
        "transaction_type": doc.transaction_type,
        "state": doc.workflow_state,
        "holder": doc.current_holder,
        "concerned_person": doc.concerned_person,
        "due_date": doc.due_date,
        "days_left": _days_left(doc.due_date, today_date),
        "external_letter_number": doc.external_letter_number,
        "external_letter_date": doc.external_letter_date,
        "page_count": doc.page_count,
        "registered_on": doc.registered_on,
        "closed_on": doc.closed_on,
        "reopened_on": doc.reopened_on,
        "sealed": bool(doc.record_sealed_on),
        "sealed_on": doc.record_sealed_on,
        "sealed_by": doc.record_sealed_by,
        "integrity_hash": doc.integrity_hash,
        "seal_reason": doc.seal_reason,
        "kpis": kpis,
        "referrals": decorated,
        "approvals": [dict(row) for row in approvals],
        "links": _link_rows(doc),
        "activity": _activity_rows(doc),
        "attachments_total": len(attachments),
        "attachments_secret": secret_count,
        "route": f"/app/murasalat-correspondence/{doc.name}",
    }

    return {
        "html": render("correspondence.html", **context),
        "indicators": _correspondence_indicators(kpis, approvals, context["sealed"]),
        "kpis": kpis,
    }


def _correspondence_indicators(kpis: dict, approvals: list, sealed: bool) -> list[dict]:
    indicators = []

    if kpis["open"]:
        indicators.append({"label": f"إحالات مفتوحة: {kpis['open']}", "color": "blue"})
    else:
        indicators.append({"label": "لا إحالات مفتوحة", "color": "gray"})

    if kpis["overdue"]:
        indicators.append({"label": f"متأخرة: {kpis['overdue']}", "color": "red"})

    if kpis["due_today"]:
        indicators.append({"label": f"تستحق اليوم: {kpis['due_today']}", "color": "orange"})

    pending = [
        row
        for row in approvals
        if (row.get("workflow_state") or "").lower() not in {"approved", "rejected"}
        and not row.get("approved_on")
    ]
    if pending:
        indicators.append({"label": f"طلبات اعتماد معلّقة: {len(pending)}", "color": "orange"})

    if sealed:
        indicators.append({"label": "مختومة", "color": "green"})

    return indicators


def referral_overview(referral: str) -> dict:
    """Everything recorded against one referral, including its own lifecycle trail."""
    doc = frappe.get_doc("Murasalat Referral", referral)
    doc.check_permission("read")

    today_date = frappe.utils.getdate(frappe.utils.today())

    # The parent file may be readable, or not: the referral is a separate document.
    parent = None
    if doc.correspondence:
        rows = frappe.get_list(
            "Murasalat Correspondence",
            filters={"name": doc.correspondence},
            fields=[
                "name",
                "subject",
                "correspondence_direction",
                "current_holder",
                "workflow_state",
                "due_date",
                "confidentiality",
                "importance",
                "record_sealed_on",
            ],
            ignore_permissions=False,
            limit_page_length=1,
        )
        parent = dict(rows[0]) if rows else None

    siblings = []
    approvals = []
    activity = []

    if doc.correspondence:
        siblings = frappe.get_list(
            "Murasalat Referral",
            filters={"correspondence": doc.correspondence, "name": ["!=", doc.name]},
            fields=REFERRAL_FIELDS,
            ignore_permissions=False,
            limit_page_length=0,
            order_by="due_date asc, creation asc",
        )

        approvals = frappe.get_list(
            "Murasalat Approval Request",
            filters={"correspondence": doc.correspondence},
            fields=APPROVAL_FIELDS,
            ignore_permissions=False,
            limit_page_length=0,
            order_by="approval_level asc, creation asc",
        )

        if parent:
            parent_doc = frappe.get_doc("Murasalat Correspondence", doc.correspondence)
            parent_doc.check_permission("read")
            activity = _activity_rows(
                parent_doc,
                referral_numbers={doc.name, doc.referral_number},
            )

    days_left = _days_left(doc.due_date, today_date)
    is_open = bool(doc.sent_on) and not doc.completed_on

    context = {
        "name": doc.name,
        "referral_number": doc.referral_number or doc.name,
        "correspondence": doc.correspondence,
        "recipient_type_ar": RECIPIENT_TYPE_AR.get(doc.recipient_type, doc.recipient_type or "—"),
        "recipient_label": doc.recipient_user or doc.recipient_department or "—",
        "direction": doc.direction,
        "importance": doc.importance,
        "state": doc.workflow_state,
        "due_date": doc.due_date,
        "days_left": days_left,
        "is_open": is_open,
        "is_overdue": bool(is_open and days_left is not None and days_left < 0),
        "is_due_today": bool(is_open and days_left == 0),
        "is_draft": not doc.sent_on,
        "sent_on": doc.sent_on,
        "received_on": doc.received_on,
        "received_by": doc.received_by,
        "completed_on": doc.completed_on,
        "completed_by": doc.completed_by,
        "instructions": doc.instructions,
        "private_referral": doc.private_referral,
        "follow_up": doc.follow_up,
        "paper_copy": doc.paper_copy,
        "cc_copy": doc.cc_copy,
        "parent": parent,
        "parent_direction_ar": (
            DIRECTION_AR.get(parent.get("correspondence_direction"), parent.get("correspondence_direction"))
            if parent
            else None
        ),
        "siblings": decorate_referrals(siblings, today_date),
        "approvals": [dict(row) for row in approvals],
        "activity": activity,
        "route": f"/app/murasalat-referral/{doc.name}",
    }

    indicators = []
    if context["is_draft"]:
        indicators.append({"label": "مسوّدة — لم تُرسل", "color": "gray"})
    if context["is_overdue"]:
        indicators.append({"label": f"متأخرة {-days_left} يومًا", "color": "red"})
    elif context["is_due_today"]:
        indicators.append({"label": "تستحق اليوم", "color": "orange"})
    elif is_open and days_left is not None:
        indicators.append({"label": f"متبقٍ {days_left} يومًا", "color": "blue"})
    if doc.completed_on:
        indicators.append({"label": "مكتملة", "color": "green"})
    if doc.private_referral:
        indicators.append({"label": "خاصة", "color": "purple"})
    if parent is None and doc.correspondence:
        indicators.append({"label": "المعاملة مقيّدة", "color": "gray"})

    return {
        "html": render("referral.html", **context),
        "indicators": indicators,
        "kpis": {"siblings": len(siblings)},
    }
