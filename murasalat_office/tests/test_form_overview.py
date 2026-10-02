"""Contract tests for the on-form overview panels.

The panels are server-rendered, which is what makes them testable: the templates are
rendered here with the real Jinja environment and asserted on, and the counters are
pure standard-library code. What cannot be asserted without a Bench — that Desk injects
the HTML into the field — is covered by source contract on the two client scripts.
"""
import importlib.util
import json
import sys
import types
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT
TODAY = date(2026, 9, 23)


def _load_overview():
    """Load services/overview.py with a stub frappe, so no Bench is needed."""
    previous = sys.modules.get("frappe")
    if previous is None:
        sys.modules["frappe"] = types.ModuleType("frappe")
    try:
        spec = importlib.util.spec_from_file_location(
            "mo_overview_under_test", APP / "services/overview.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        if previous is None:
            sys.modules.pop("frappe", None)
        else:
            sys.modules["frappe"] = previous


def _row(**values):
    return values


# --------------------------------------------------------------------------- counters


def test_referral_kpis_counts_each_bucket():
    mod = _load_overview()

    rows = [
        _row(name="MR-1", sent_on="2026-09-01", due_date="2026-09-20"),
        _row(name="MR-2", sent_on="2026-09-01", due_date="2026-09-23"),
        _row(name="MR-3", sent_on="2026-09-01", due_date="2026-09-30"),
        _row(name="MR-4"),
        _row(
            name="MR-5",
            sent_on="2026-09-01",
            completed_on="2026-09-10",
            due_date="2026-09-12",
        ),
    ]

    assert mod.referral_kpis(rows, TODAY) == {
        "total": 5,
        "draft": 1,
        "open": 3,
        "overdue": 1,
        "due_today": 1,
        "completed": 1,
    }


def test_completed_referral_is_not_counted_as_overdue():
    """A finished referral past its due date is done, not late."""
    mod = _load_overview()

    rows = [
        _row(
            name="MR-9",
            sent_on="2026-08-01",
            received_on="2026-08-02",
            completed_on="2026-08-10",
            due_date="2026-08-05",
        )
    ]

    kpis = mod.referral_kpis(rows, TODAY)

    assert kpis["completed"] == 1
    assert kpis["open"] == 0
    assert kpis["overdue"] == 0


def test_kpis_tolerate_datetime_strings_and_missing_due_dates():
    mod = _load_overview()

    rows = [
        _row(name="MR-1", sent_on="2026-09-01 08:30:00", due_date="2026-09-20 00:00:00"),
        _row(name="MR-2", sent_on="2026-09-01", due_date=None),
    ]

    kpis = mod.referral_kpis(rows, TODAY)

    assert kpis["overdue"] == 1
    assert kpis["open"] == 2


def test_decorate_referrals_marks_each_state_once():
    mod = _load_overview()

    rows = [
        _row(name="A", sent_on="2026-09-01", due_date="2026-09-20", recipient_type="User", recipient_user="u@example.com"),
        _row(name="B", sent_on="2026-09-01", due_date="2026-09-23", recipient_type="Department", recipient_department="ORG-1"),
        _row(name="C", sent_on="2026-09-01", completed_on="2026-09-02", due_date="2026-09-05"),
        _row(name="D", recipient_type="User", recipient_user="z@example.com"),
    ]

    decorated = {row["name"]: row for row in mod.decorate_referrals(rows, TODAY)}

    assert decorated["A"]["is_overdue"] and not decorated["A"]["is_due_today"]
    assert decorated["B"]["is_due_today"]
    assert decorated["C"]["is_completed"] and not decorated["C"]["is_overdue"]
    assert decorated["D"]["is_draft"]
    assert decorated["A"]["recipient_label"] == "u@example.com"
    assert decorated["B"]["recipient_type_ar"] == "قسم"


# ---------------------------------------------------------------------------- render


def _correspondence_context(mod, **overrides):
    context = {
        "name": "MO-00001",
        "subject": "طلب موافقة على تنظيم ورشة عمل",
        "direction_ar": "وارد",
        "direction": "Incoming",
        "confidentiality": "عام",
        "importance": "متوسط",
        "transaction_type": "مذكرة",
        "state": "Registered",
        "holder": "الشؤون الإدارية",
        "concerned_person": "أحمد",
        "due_date": "2026-09-30",
        "days_left": 7,
        "external_letter_number": "122/2026",
        "external_letter_date": "2026-09-01",
        "page_count": 2,
        "registered_on": "2026-09-02 09:00:00",
        "closed_on": None,
        "reopened_on": None,
        "sealed": False,
        "sealed_on": None,
        "sealed_by": None,
        "integrity_hash": None,
        "seal_reason": None,
        "kpis": {"total": 1, "draft": 0, "open": 1, "overdue": 0, "due_today": 0, "completed": 0},
        "referrals": [
            {
                "name": "MR-00001",
                "referral_number": "MR-00001",
                "recipient_label": "الشؤون القانونية",
                "recipient_type_ar": "قسم",
                "state": "Sent",
                "due_date": "2026-09-25",
                "days_left": 2,
                "sent_on": "2026-09-20 10:00:00",
                "received_on": None,
                "completed_on": None,
                "is_draft": False,
                "is_completed": False,
                "is_open": True,
                "is_overdue": False,
                "is_due_today": False,
                "private_referral": 0,
                "follow_up": 1,
                "paper_copy": 0,
                "cc_copy": 0,
            }
        ],
        "approvals": [],
        "links": [],
        "activity": [
            {
                "activity_type": "Registered",
                "activity_type_ar": "تسجيل",
                "activity_on": "2026-09-02 09:00:00",
                "actor": "clerk@example.com",
                "details": "تم تسجيل المعاملة رسميًا",
                "referral_number": None,
            }
        ],
        "attachments_total": 2,
        "attachments_secret": 1,
        "route": "/app/murasalat-correspondence/MO-00001",
    }
    context.update(overrides)
    return context


def test_correspondence_panel_shows_referrals_kpis_and_trail():
    mod = _load_overview()

    html = mod.render("correspondence.html", **_correspondence_context(mod))

    assert "الإحالات على هذه المعاملة" in html
    assert "/app/murasalat-referral/MR-00001" in html
    assert "الشؤون القانونية" in html
    assert "إحالات مفتوحة" in html
    assert "متأخرة" in html
    assert "آخر الحركات" in html
    assert "المعاملات المرتبطة" not in html  # no links were supplied
    assert "طلبات الاعتماد" in html


def test_correspondence_panel_marks_a_sealed_record():
    mod = _load_overview()

    html = mod.render(
        "correspondence.html",
        **_correspondence_context(
            mod,
            sealed=True,
            sealed_on="2026-09-15 12:00:00",
            sealed_by="supervisor@example.com",
            seal_reason="أُقفلت بعد الأرشفة",
            integrity_hash="a" * 64,
        ),
    )

    assert "مختومة" in html
    assert "حالة الختم والسلامة" in html
    assert "supervisor@example.com" in html
    assert "a" * 64 in html


def test_correspondence_panel_escapes_user_written_content():
    """A subject or body typed by a user must never become markup."""
    mod = _load_overview()

    payload = '<script>alert("x")</script>'
    html = mod.render("correspondence.html", **_correspondence_context(mod, subject=payload))

    assert "<script>" not in html
    assert "&lt;script&gt;" in html


def _referral_context(mod, **overrides):
    context = {
        "name": "MR-00002",
        "referral_number": "MR-00002",
        "correspondence": "MO-00001",
        "recipient_type_ar": "مستخدم",
        "recipient_label": "officer@example.com",
        "direction": "Internal",
        "importance": "عاجل",
        "state": "Sent",
        "due_date": "2026-09-25",
        "days_left": 2,
        "is_open": True,
        "is_overdue": False,
        "is_due_today": False,
        "is_draft": False,
        "sent_on": "2026-09-20 10:00:00",
        "received_on": None,
        "received_by": None,
        "completed_on": None,
        "completed_by": None,
        "instructions": "يرجى مراجعة البنود وإبداء الرأي",
        "private_referral": 0,
        "follow_up": 0,
        "paper_copy": 0,
        "cc_copy": 0,
        "parent": {
            "name": "MO-00001",
            "subject": "طلب موافقة",
            "correspondence_direction": "Incoming",
            "current_holder": "الشؤون الإدارية",
            "workflow_state": "Registered",
            "due_date": "2026-09-30",
            "confidentiality": "عام",
            "importance": "متوسط",
            "record_sealed_on": None,
        },
        "parent_direction_ar": "وارد",
        "siblings": [],
        "approvals": [],
        "activity": [
            {
                "activity_type": "Referral Sent",
                "activity_type_ar": "إرسال إحالة",
                "activity_on": "2026-09-20 10:00:00",
                "actor": "clerk@example.com",
                "details": "أُرسلت إلى officer@example.com",
                "referral_number": "MR-00002",
            }
        ],
        "route": "/app/murasalat-referral/MR-00002",
    }
    context.update(overrides)
    return context


def test_referral_panel_shows_lifecycle_stamps_parent_and_trail():
    mod = _load_overview()

    html = mod.render("referral.html", **_referral_context(mod))

    assert "إحالة MR-00002" in html
    assert "أُرسلت" in html and "استُلمت" in html and "أُكملت" in html
    assert "لم تُستلم" in html  # the pending stamp is stated plainly
    assert "/app/murasalat-correspondence/MO-00001" in html
    assert "مسار هذه الإحالة" in html
    assert "إرسال إحالة" in html
    assert "التعليمات إلى المستلِم" in html


def test_referral_panel_hides_the_parent_when_it_is_not_readable():
    mod = _load_overview()

    html = mod.render(
        "referral.html",
        **_referral_context(mod, parent=None, parent_direction_ar=None, siblings=[], activity=[]),
    )

    assert "مقيّد" in html
    assert "طلب موافقة" not in html
    # no sibling names and no parent trail may leak
    assert "بقية إحالات المعاملة" in html
    assert "غير متاح" in html


def test_referral_panel_escapes_instructions():
    mod = _load_overview()

    html = mod.render(
        "referral.html",
        **_referral_context(mod, instructions='<img src=x onerror="alert(1)">'),
    )

    # the whole payload is escaped text: no tag is created, no attribute is parsed
    assert "<img" not in html
    assert "&lt;img" in html
    assert "alert(1)" in html


def test_both_panels_are_right_to_left_and_self_contained():
    mod = _load_overview()

    for template, context in (
        ("correspondence.html", _correspondence_context(mod)),
        ("referral.html", _referral_context(mod)),
    ):
        html = mod.render(template, **context)
        assert "mo-ov" in html
        assert "direction: rtl" in html
        assert "<style>" in html
        # the panel must not depend on any external asset being loaded
        assert "<link" not in html and "<script" not in html


def test_panels_render_without_any_optional_data():
    """A brand-new record with no referrals, approvals, links or activity must render."""
    mod = _load_overview()

    empty_kpis = {"total": 0, "draft": 0, "open": 0, "overdue": 0, "due_today": 0, "completed": 0}

    correspondence = mod.render(
        "correspondence.html",
        **_correspondence_context(
            mod, kpis=empty_kpis, referrals=[], approvals=[], links=[], activity=[],
            attachments_total=0, attachments_secret=0, sealed=False,
        ),
    )
    assert "لا توجد إحالات مسجّلة" in correspondence
    assert "لا توجد حركات مسجّلة" in correspondence

    referral = mod.render(
        "referral.html",
        **_referral_context(mod, is_draft=True, sent_on=None, activity=[], siblings=[]),
    )
    assert "مسوّدة" in referral
    assert "لم تُرسل" in referral


# ------------------------------------------------------------------------- contracts


def test_indicators_are_native_frappe_colors():
    mod = _load_overview()

    allowed = {"green", "orange", "red", "blue", "gray", "purple", "pink", "yellow"}
    kpis = {"total": 3, "draft": 1, "open": 2, "overdue": 1, "due_today": 1, "completed": 0}
    approvals = [{"name": "MAR-1", "workflow_state": "Pending", "approved_on": None}]

    indicators = mod._correspondence_indicators(kpis, approvals, sealed=True)

    for indicator in indicators:
        assert indicator["color"] in allowed
        assert indicator["label"]

    named = {indicator["label"]: indicator["color"] for indicator in indicators}
    assert named["متأخرة: 1"] == "red"
    assert named["تستحق اليوم: 1"] == "orange"
    assert named["مختومة"] == "green"


def test_endpoints_are_whitelisted_and_check_permission():
    source = (APP / "api/operations.py").read_text()

    for name in ("correspondence_overview", "referral_overview"):
        assert f"def {name}(" in source, name
        assert "whitelist" in source.split(f"def {name}(")[0][-200:], name

    overview = (APP / "services/overview.py").read_text()
    assert overview.count('check_permission("read")') >= 2
    assert "ignore_permissions=False" in overview
    # this module must never widen access
    assert "ignore_permissions=True" not in overview
    assert "ignore_permissions = True" not in overview


def test_overview_reads_through_native_permission_aware_apis():
    overview = (APP / "services/overview.py").read_text()

    assert "frappe.get_list(" in overview
    assert "frappe.get_doc(" in overview
    # no hand-written SQL and no bypass of the ORM
    assert "frappe.db.sql" not in overview
    assert "frappe.db.get_all" not in overview


def test_open_referral_state_is_derived_not_stored():
    """A referral's openness is derived, and stored nowhere.

    It used to be derived from `sent_on` alone. A row migrated from the child table carries the
    workflow state and no timestamp, so that rule called a sent referral a draft - and the panel
    contradicted the badge printed beside it. The two sources are now read together.
    """
    from pathlib import Path

    source = (
        Path(__file__).resolve().parents[1] / "services/overview.py"
    ).read_text(encoding="utf-8")

    assert "_is_sent(" in source and "_is_completed(" in source
    assert "not row.get(\"sent_on\")" not in source
    assert "bool(doc.sent_on)" not in source
    assert "not doc.sent_on" not in source


def test_both_forms_carry_an_overview_field_first_in_the_layout():
    for slug in ("murasalat_correspondence", "murasalat_referral"):
        data = json.loads(
            (APP / f"murasalat_office/doctype/{slug}/{slug}.json").read_text()
        )
        fields = {field["fieldname"]: field for field in data["fields"]}

        assert "overview_html" in fields, slug
        assert fields["overview_html"]["fieldtype"] == "HTML", slug
        # the panel is the first thing on the form
        assert data["field_order"][0] == "overview_html", slug


def test_client_scripts_call_the_right_endpoints_and_field():
    scripts = {
        "murasalat_correspondence": "correspondence_overview",
        "murasalat_referral": "referral_overview",
    }

    for slug, endpoint in scripts.items():
        source = (APP / f"murasalat_office/doctype/{slug}/{slug}.js").read_text()

        assert f"murasalat_office.api.operations.{endpoint}" in source, slug
        assert '"overview_html"' in source, slug
        assert "$wrapper" in source, slug
        # native Frappe dashboard indicators, not a hand-rolled badge row
        assert "frm.dashboard.add_indicator" in source, slug
        assert "get_field(fieldname)" in source, slug


def test_overview_introduces_no_governance_or_doctype():
    hooks = (APP / "hooks.py").read_text()
    assert "fixtures = [" not in hooks

    # presentation only: no new DocType, no role, no permission row
    new_doctypes = [
        path.name
        for path in (APP / "murasalat_office/doctype").glob("*")
        if path.is_dir() and path.name == "murasalat_overview"
    ]
    assert new_doctypes == []
