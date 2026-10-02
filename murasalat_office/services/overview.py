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
from datetime import date, datetime
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
    "completion_result",
    "received_by",
    "completed_by",
    "private_referral",
    "follow_up",
    "paper_copy",
    "cc_copy",
    "cancelled_on",
    "cancel_reason",
    "instructions",
    "creation",
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


REPLY_LINK_FIELDS = [
    "parent",
    "linked_correspondence",
    "relationship_type",
    "link_order",
]

REPLY_FIELDS = [
    "name",
    "subject",
    "correspondence_direction",
    "outgoing_source_entity",
    "outgoing_target_entry",
    "transaction_type",
    "importance",
    "confidentiality",
    "workflow_state",
    "external_letter_number",
    "external_letter_date",
    "registered_on",
    "closed_on",
    "creation",
]


def _reply_kpis(rows: Iterable[dict]) -> dict[str, int]:
    """Return presentation counters for official replies to an incoming record."""
    kpis = {
        "total": 0,
        "draft": 0,
        "registered": 0,
        "closed": 0,
    }

    for row in rows:
        kpis["total"] += 1

        if row.get("registered_on"):
            kpis["registered"] += 1
        else:
            kpis["draft"] += 1

        if row.get("closed_on"):
            kpis["closed"] += 1

    return kpis


def _approval_summary(rows: Iterable[dict]) -> dict[str, Any]:
    """Summarize approval state without inventing a second approval system."""
    total = 0
    pending = 0
    approved = 0
    rejected = 0

    for row in rows:
        total += 1
        state = (row.get("workflow_state") or "").strip().lower()
        if state == "approved" or row.get("approved_on"):
            approved += 1
        elif state == "rejected":
            rejected += 1
        else:
            pending += 1

    if pending:
        label = "بانتظار الاعتماد"
        css = "orange"
    elif rejected:
        label = "مرفوض"
        css = "red"
    elif approved and total:
        label = "معتمد"
        css = "green"
    else:
        label = "لا يوجد اعتماد"
        css = "gray"

    return {
        "total": total,
        "pending": pending,
        "approved": approved,
        "rejected": rejected,
        "label": label,
        "css": css,
    }


def _operational_status(
    doc,
    referral_kpis: dict,
    reply_kpis: dict,
    approval_summary: dict,
    today_date: date,
) -> dict[str, str]:
    """Derive a read-only operational state from existing native records."""
    if doc.record_sealed_on:
        return {"key": "sealed", "label": "مختومة", "css": "green", "detail": "المعاملة مختومة ومحفوظة كسجل نهائي."}

    if referral_kpis["open"]:
        if referral_kpis["overdue"]:
            return {"key": "referrals_overdue", "label": "إحالات متأخرة", "css": "red", "detail": f"يوجد {referral_kpis['overdue']} إحالة متأخرة."}
        return {"key": "referrals_open", "label": "بانتظار إكمال الإحالات", "css": "blue", "detail": f"يوجد {referral_kpis['open']} إحالة مفتوحة."}

    if doc.closed_on:
        return {"key": "closed", "label": "مغلقة", "css": "green", "detail": "تم إغلاق المعاملة."}

    if doc.correspondence_direction == "Incoming":
        if reply_kpis["draft"]:
            return {"key": "reply_draft", "label": "يوجد رد مسودة", "css": "orange", "detail": "يوجد رد رسمي مسودة يحتاج إلى مراجعة."}
        if reply_kpis["registered"]:
            return {"key": "reply_registered", "label": "يوجد رد رسمي", "css": "green", "detail": "تم إنشاء رد رسمي لهذه المعاملة."}
        due_left = _days_left(doc.due_date, today_date)
        if due_left is not None and due_left < 0:
            days = -due_left
            return {"key": "correspondence_overdue", "label": "المعاملة متأخرة", "css": "red", "detail": f"تجاوزت الموعد النهائي بمقدار {days} يومًا."}
        return {"key": "ready_for_reply", "label": "جاهزة لإنشاء الرد", "css": "green", "detail": "لا توجد إحالات مفتوحة ويمكن إنشاء رد رسمي."}

    if approval_summary["rejected"]:
        return {"key": "approval_rejected", "label": "الاعتماد مرفوض", "css": "red", "detail": "يوجد طلب اعتماد مرفوض يحتاج إلى معالجة."}

    if approval_summary["pending"]:
        return {"key": "approval_pending", "label": "بانتظار الاعتماد", "css": "orange", "detail": f"يوجد {approval_summary['pending']} طلب اعتماد معلّق."}

    return {"key": "in_progress", "label": "قيد المعالجة", "css": "blue", "detail": "المعاملة قيد المعالجة."}


def _correspondence_age(doc, today_date: date) -> dict[str, Any]:
    """Return elapsed calendar days from registration to close/today."""
    start = _as_date(doc.registered_on)
    end = _as_date(doc.closed_on) or today_date
    if not start:
        return {"days": None, "label": "غير مسجلة بعد"}
    days = max((end - start).days, 0)
    return {"days": days, "label": f"{days} يومًا"}


def _get_replies(correspondence: str) -> list[dict]:
    """Return visible official replies by querying the parent DocType.

    ``Murasalat Correspondence Link`` is a child table, not an independent business
    record. The authoritative record is the Outgoing ``Murasalat Correspondence``
    itself. Querying the parent and filtering through ``links.*`` lets Frappe apply
    the parent document's normal read permissions while retaining the existing
    ``Reply To`` relationship as the single source of truth.

    Frappe v16 Query Builder supports filtering parent records through Child Table
    fields. ``distinct=True`` prevents duplicate parents if more than one matching
    child row ever exists.
    """
    replies = frappe.qb.get_query(
        "Murasalat Correspondence",
        fields=REPLY_FIELDS,
        filters=[
            ["correspondence_direction", "=", "Outgoing"],
            ["links.linked_correspondence", "=", correspondence],
            ["links.relationship_type", "=", "Reply To"],
        ],
        distinct=True,
        ignore_permissions=False,
    ).run(as_dict=True)

    replies = sorted(
        replies,
        key=lambda row: (row.get("creation") or "", row.get("name") or ""),
    )

    decorated = []

    for row in replies:
        item = dict(row)

        if row.get("closed_on"):
            item["status_label"] = "مغلقة"
            item["status_class"] = "orange"
        elif row.get("registered_on"):
            item["status_label"] = "مسجّلة"
            item["status_class"] = "green"
        else:
            item["status_label"] = "مسوّدة"
            item["status_class"] = "gray"

        decorated.append(item)

    return decorated


def _as_date(value: Any) -> date | None:
    """Coerce a database value to a date without touching Frappe."""
    if not value:
        return None
    # ``datetime`` is a subclass of ``date`` in Python, so it must be
    # handled before the plain-date check. Frappe Datetime fields commonly
    # arrive here as ``datetime`` objects while ``today_date`` is a ``date``.
    if isinstance(value, datetime):
        return value.date()
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

        if not _is_sent(row):
            kpis["draft"] += 1
            continue

        if _is_closed_referral(row):
            continue

        if _is_completed(row):
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



def _attachment_rows(doc):
    """Attachments as the referral panel reads them, with secret files withheld.

    The row exists so an operator can see that a secret attachment is on the record; the
    file name is not printed, because the panel is readable by anyone who may read the
    referral.
    """
    rows = []

    for row in (getattr(doc, "attachments", None) or []):
        is_secret = bool(getattr(row, "is_secret", None))
        file_url = getattr(row, "file", None) or ""

        rows.append(
            {
                "attachment_type": getattr(row, "attachment_type", None),
                "archive_location": getattr(row, "archive_location", None),
                "is_secret": is_secret,
                "label": (
                    "مرفق سرّي — يُطلب من الأرشيف"
                    if is_secret
                    else file_url.rsplit("/", 1)[-1]
                ),
            }
        )

    return rows

def _is_sent(row) -> bool:
    """Whether a referral counts as sent.

    The lifecycle evidence is the timestamp itself. Workflow state is intentionally not
    interpreted here because each organization may define its own Referral Workflow.
    """
    return bool(row.get("sent_on"))


def _is_completed(row) -> bool:
    """Whether a referral has a recorded completion event."""
    return bool(row.get("completed_on"))


def _is_closed_referral(row) -> bool:
    """A cancellation timestamp closes referral work without interpreting Workflow state."""
    return bool(row.get("cancelled_on"))


def decorate_referrals(rows: Iterable[dict], today_date: date) -> list[dict]:
    """Add the presentation-only fields the template needs."""
    decorated = []

    for row in rows:
        item = dict(row)
        item["days_left"] = _days_left(row.get("due_date"), today_date)
        item["is_draft"] = not _is_sent(row)
        item["is_completed"] = _is_completed(row)
        item["is_open"] = (
            _is_sent(row) and not _is_completed(row) and not _is_closed_referral(row)
        )
        item["is_overdue"] = bool(item["is_open"] and item["days_left"] is not None and item["days_left"] < 0)
        item["is_due_today"] = bool(item["is_open"] and item["days_left"] == 0)
        item["recipient_label"] = (
            row.get("recipient_user") or row.get("recipient_department") or "—"
        )
        item["recipient_type_ar"] = RECIPIENT_TYPE_AR.get(
            row.get("recipient_type"), row.get("recipient_type") or "—"
        )
        item = _decorate_referral_status(item)
        decorated.append(item)

    return decorated


def _decorate_referral_status(item: dict) -> dict:
    """Add neutral lifecycle presentation without interpreting Workflow states."""
    if item.get("cancelled_on"):
        item["status_label"] = "ملغاة"
        item["status_class"] = "red"
    elif item.get("completed_on"):
        item["status_label"] = "مكتملة"
        item["status_class"] = "green"
    elif not item.get("sent_on"):
        item["status_label"] = "مسوّدة"
        item["status_class"] = "gray"
    elif item.get("is_overdue"):
        item["status_label"] = "متأخرة"
        item["status_class"] = "red"
    elif item.get("is_due_today"):
        item["status_label"] = "تستحق اليوم"
        item["status_class"] = "orange"
    else:
        item["status_label"] = "قيد التنفيذ"
        item["status_class"] = "blue"
    return item


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
    """Render overview templates while remaining compatible with older callers/tests."""
    if template_name == "correspondence.html":
        kpis = context.get("kpis") or {
            "total": 0,
            "draft": 0,
            "open": 0,
            "overdue": 0,
            "due_today": 0,
            "completed": 0,
        }
        replies = context.get("replies") or []
        approvals = context.get("approvals") or []
        context.setdefault("reply_kpis", _reply_kpis(replies))
        context.setdefault("approval_summary", _approval_summary(approvals))

        if "operational_status" not in context:
            class _FallbackDoc:
                correspondence_direction = context.get("direction")
                workflow_state = context.get("state")
                record_sealed_on = context.get("sealed_on")
                closed_on = context.get("closed_on")
                due_date = context.get("due_date")

            fallback_today = (
                frappe.utils.getdate(frappe.utils.today())
                if hasattr(frappe, "utils")
                else date.today()
            )
            context["operational_status"] = _operational_status(
                _FallbackDoc(),
                kpis,
                context["reply_kpis"],
                context["approval_summary"],
                fallback_today,
            )

        if "correspondence_age" not in context:
            registered = _as_date(context.get("registered_on"))
            closed = _as_date(context.get("closed_on"))
            today = frappe.utils.getdate(frappe.utils.today()) if hasattr(frappe, "utils") else date.today()
            if registered:
                days = max(((closed or today) - registered).days, 0)
                context["correspondence_age"] = {"days": days, "label": f"{days} يومًا"}
            else:
                context["correspondence_age"] = {"days": None, "label": "غير مسجلة بعد"}

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


def correspondence_overview(correspondence: str, section: str = "overview") -> dict:
    """Render one native DocType-tab panel for a correspondence, for a non-Administrator user."""
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

    # "حالتي" is intentionally limited to a direct user recipient. Department-level
    # membership is organization-specific and must not be guessed by this UI.
    current_user = frappe.session.user
    cancelled_count = sum(1 for row in decorated if row.get("cancelled_on"))
    my_referrals = [row for row in decorated if row.get("recipient_user") == current_user]
    my_open = [row for row in my_referrals if row.get("is_open")]
    my_overdue = [row for row in my_open if row.get("is_overdue")]

    # Replies are reverse-linked through the existing Reply To child-table row.
    # They are displayed only for Incoming correspondence.
    replies = _get_replies(doc.name) if doc.correspondence_direction == "Incoming" else []
    reply_kpis = _reply_kpis(replies)
    approval_summary = _approval_summary(approvals)
    operational_status = _operational_status(doc, kpis, reply_kpis, approval_summary, today_date)
    correspondence_age = _correspondence_age(doc, today_date)

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
        "my_referrals": my_referrals,
        "cancelled_count": cancelled_count,
        "my_open": len(my_open),
        "my_overdue": len(my_overdue),
        "replies": replies,
        "reply_kpis": reply_kpis,
        "approval_summary": approval_summary,
        "operational_status": operational_status,
        "correspondence_age": correspondence_age,
        "approvals": [dict(row) for row in approvals],
        "links": _link_rows(doc),
        "activity": _activity_rows(doc),
        "attachments_total": len(attachments),
        "attachments_secret": secret_count,
        "route": f"/app/murasalat-correspondence/{doc.name}",
    }

    allowed_sections = {"overview", "referrals", "replies", "tracking", "activity"}
    if section not in allowed_sections:
        section = "overview"
    context["experience_section"] = section

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
    is_open = _is_sent(doc) and not _is_completed(doc) and not _is_closed_referral(doc)

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
        "is_draft": not _is_sent(doc),
        "sent_on": doc.sent_on,
        "received_on": doc.received_on,
        "received_by": doc.received_by,
        "completed_on": doc.completed_on,
        "completion_result": doc.completion_result,
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
    if _is_closed_referral(doc):
        indicators.append({"label": "ملغاة", "color": "gray"})
    elif _is_completed(doc):
        indicators.append({"label": "مكتملة", "color": "green"})
    if doc.private_referral:
        indicators.append({"label": "خاصة", "color": "purple"})
    if parent is None and doc.correspondence:
        indicators.append({"label": "المعاملة مقيّدة", "color": "gray"})

    # Attachment rows for the panel, assigned after the literal so the panel can grow
    # without touching the context definition above.
    context["attachments"] = _attachment_rows(doc)
    context["attachments_total"] = len(getattr(doc, "attachments", None) or [])
    context["attachments_secret"] = sum(
        1 for r in (getattr(doc, "attachments", None) or []) if getattr(r, "is_secret", None)
    )

    return {
        "html": render("referral.html", **context),
        "indicators": indicators,
        "kpis": {"siblings": len(siblings)},
    }
