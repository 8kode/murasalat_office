"""Contract tests for the operational reports.

Two kinds of assertion here:

* the pure helpers in ``services/aging.py`` are exercised directly, because the ageing
  and volume rules are the part that can be wrong in a way nobody notices;
* the report modules and metadata are pinned by contract, including the positional
  Script Report return value that three existing reports got wrong.
"""
import json
import re
from pathlib import Path
from sys import path as sys_path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT
REPORTS = APP / "murasalat_office/report"

# import the pure helper module by path so no Frappe stub is needed
sys_path.insert(0, str(APP.parent))
from murasalat_office.services import aging

NEW_REPORTS = [
    ("murasalat_correspondence_register", "Murasalat Correspondence Register"),
    ("murasalat_referral_aging", "Murasalat Referral Aging"),
]


# ---------------------------------------------------------------- pure ageing helpers


def test_aging_buckets_cover_every_boundary():
    assert aging.aging_bucket(None) == "not_due"
    assert aging.aging_bucket(-5) == "not_due"
    assert aging.aging_bucket(0) == "not_due"
    assert aging.aging_bucket(1) == "0-3"
    assert aging.aging_bucket(3) == "0-3"
    assert aging.aging_bucket(4) == "4-7"
    assert aging.aging_bucket(7) == "4-7"
    assert aging.aging_bucket(8) == "8-14"
    assert aging.aging_bucket(14) == "8-14"
    assert aging.aging_bucket(15) == "15+"
    assert aging.aging_bucket(365) == "15+"


def test_days_late_handles_datetimes_missing_dates_and_future_due_dates():
    assert aging.days_late("2026-09-01", "2026-09-23") == 22
    assert aging.days_late("2026-09-23 10:00:00", "2026-09-23") == 0
    assert aging.days_late("2026-09-30", "2026-09-23") == -7
    assert aging.days_late(None, "2026-09-23") is None
    assert aging.days_late("2026-09-01", None) is None


def test_summarize_aging_counts_buckets_and_the_worst_case():
    rows = [
        {"due_date": "2026-09-20"},   # 3 days late
        {"due_date": "2026-09-10"},   # 13 days late
        {"due_date": "2026-08-20"},   # 34 days late
        {"due_date": "2026-09-30"},   # inside due date
        {"due_date": None},           # no due date
    ]

    summary = aging.summarize_aging(rows, "2026-09-23")

    assert summary["total_open"] == 5
    assert summary["overdue"] == 3
    assert summary["worst_days"] == 34
    assert summary["within_due"] == 1
    assert summary["without_due_date"] == 1
    assert summary["buckets"]["0-3"] == 1
    assert summary["buckets"]["8-14"] == 1
    assert summary["buckets"]["15+"] == 1
    assert summary["buckets"]["4-7"] == 0


def test_monthly_volume_groups_by_month_and_orders_them():
    values = [
        "2026-09-01",
        "2026-09-23 12:00:00",
        "2026-08-05",
        "2026-10-01",
        None,
    ]

    volume = aging.monthly_volume(values)

    assert volume == {"2026-08": 1, "2026-09": 2, "2026-10": 1}
    assert aging.ordered_months(volume) == ["2026-08", "2026-09", "2026-10"]


def test_month_labels_are_arabic_and_fall_back_safely():
    assert aging.month_label("2026-09") == "سبتمبر 2026"
    assert aging.month_label("2026-01") == "يناير 2026"
    assert aging.month_label("not-a-month") == "not-a-month"


# --------------------------------------------------------- frappe chart / summary shape


def test_frappe_chart_matches_the_shape_the_report_view_reads():
    """query_report.js reads chart.data.labels — anything else renders nothing."""
    chart = aging.frappe_chart(["سبتمبر 2026"], [4], "المعاملات", "bar")

    assert set(chart) == {"data", "type", "fieldtype"}
    assert chart["data"]["labels"] == ["سبتمبر 2026"]
    assert chart["data"]["datasets"] == [{"name": "المعاملات", "values": [4]}]
    assert chart["type"] == "bar"
    assert chart["fieldtype"] == "Int"


def test_frappe_chart_returns_none_instead_of_a_blank_card():
    assert aging.frappe_chart([], [], "x") is None
    assert aging.frappe_chart(["a"], [1], "x", "not-a-type") is None


def test_summary_items_carry_label_value_and_optional_indicator():
    plain = aging.summary_item("إجمالي", 12)
    flagged = aging.summary_item("متأخرة", 3, indicator="Red")

    assert plain == {"label": "إجمالي", "value": 12, "datatype": "Int"}
    assert flagged["indicator"] == "Red"


def test_bucket_chart_lists_every_band_in_order_even_when_zero():
    chart = aging.bucket_chart({"15+": 2, "not_due": 5})

    labels = chart["data"]["labels"]
    assert labels == [aging.AGE_BUCKET_LABELS[bucket] for bucket in aging.AGE_BUCKETS]
    assert len(labels) == 5
    assert chart["data"]["datasets"][0]["values"] == [5, 0, 0, 0, 2]


# ------------------------------------------------------------------- return contract


def test_the_three_reports_that_misfiled_their_summary_are_fixed():
    """The fourth value is ``chart``; a summary passed there is silently dropped."""
    for slug in (
        "murasalat_work_queue",
        "murasalat_overdue_referrals",
        "murasalat_inbox",
    ):
        source = (REPORTS / slug / f"{slug}.py").read_text()

        assert "return columns, data, None, summary" not in source, slug
        assert re.search(r"return\s+\w+\(\)?[^,]*,\s*data[^,]*,\s*None,\s*None,\s*summary", source) or \
            "None, None, summary" in source or "_result(data)" in source, slug


def test_new_reports_use_the_six_value_positional_contract():
    for slug, _ in NEW_REPORTS:
        source = (REPORTS / slug / f"{slug}.py").read_text()
        assert "return _columns(), data, None, chart, summary" in source or \
               "return _columns(), data, None, bucket_chart(counts), summary" in source, slug


def test_every_report_returns_a_chart_or_summary_where_it_matters():
    register = (REPORTS / "murasalat_correspondence_register/murasalat_correspondence_register.py").read_text()
    aging_report = (REPORTS / "murasalat_referral_aging/murasalat_referral_aging.py").read_text()

    assert "frappe_chart(" in register
    assert "monthly_volume(" in register
    assert "bucket_chart(" in aging_report
    assert "summarize_aging(" not in aging_report  # the report buckets per row itself


# ---------------------------------------------------------------------------- metadata


def test_new_report_metadata_is_complete():
    for slug, name in NEW_REPORTS:
        folder = REPORTS / slug
        assert (folder / f"{slug}.py").is_file(), slug
        assert (folder / f"{slug}.js").is_file(), slug

        data = json.loads((folder / f"{slug}.json").read_text())
        assert data["doctype"] == "Report", slug
        assert data["name"] == name, slug
        assert data["report_name"] == name, slug
        assert data["report_type"] == "Script Report", slug
        assert data["is_standard"] == "Yes", slug
        assert data["ref_doctype"], slug
        assert data["module"] == "Murasalat Office", slug
        assert data["disabled"] == 0, slug


def test_new_reports_target_the_right_doctype():
    register = json.loads(
        (REPORTS / "murasalat_correspondence_register/murasalat_correspondence_register.json").read_text()
    )
    aging_report = json.loads(
        (REPORTS / "murasalat_referral_aging/murasalat_referral_aging.json").read_text()
    )

    assert register["ref_doctype"] == "Murasalat Correspondence"
    assert aging_report["ref_doctype"] == "Murasalat Referral"


def test_every_report_has_its_client_script():
    for folder in sorted(REPORTS.iterdir()):
        if not folder.is_dir() or folder.name == "__pycache__":
            continue
        assert (folder / f"{folder.name}.js").is_file(), folder.name


def test_new_report_filters_are_present_and_practical():
    register = (REPORTS / "murasalat_correspondence_register/murasalat_correspondence_register.js").read_text()
    aging_js = (REPORTS / "murasalat_referral_aging/murasalat_referral_aging.js").read_text()

    for fieldname in ("from_date", "to_date", "correspondence_direction", "current_holder", "sealing"):
        assert f'fieldname: "{fieldname}"' in register, fieldname

    # the measuring date is the whole point of an ageing report
    assert 'fieldname: "as_of_date"' in aging_js
    assert "reqd: 1" in aging_js
    assert 'fieldname: "only_overdue"' in aging_js


# ------------------------------------------------------------------------- guardrails


def test_reports_stay_permission_aware():
    for slug, _ in NEW_REPORTS:
        source = (REPORTS / slug / f"{slug}.py").read_text()

        assert "ignore_permissions=False" in source, slug
        assert "ignore_permissions=True" not in source, slug
        assert "frappe.db.sql" not in source, slug
        assert "frappe.get_all(" not in source, slug


def test_report_queries_never_disable_totals_silently():
    for slug, _ in NEW_REPORTS:
        source = (REPORTS / slug / f"{slug}.py").read_text()
        assert "skip_total_row" not in source, slug


def test_new_reports_introduce_no_doctype_change_or_governance():
    hooks = (APP / "hooks.py").read_text()
    assert "fixtures = [" not in hooks
    assert not (APP / "fixtures").exists()

    for slug, _ in NEW_REPORTS:
        data = json.loads((REPORTS / slug / f"{slug}.json").read_text())
        # a report may not ship role rows as a side effect of being added
        assert "permissions" not in data, slug


def test_arabic_band_labels_are_all_present():
    for bucket in aging.AGE_BUCKETS:
        assert aging.AGE_BUCKET_LABELS[bucket].strip(), bucket
    assert len(set(aging.AGE_BUCKET_LABELS.values())) == len(aging.AGE_BUCKETS)
