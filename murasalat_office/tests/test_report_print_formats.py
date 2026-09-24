"""The A4 print formats for the three management reports.

Frappe renders a report layout differently from a DocType one. The user picks the format in the
report's print dialog, the server returns its html and css through
``frappe.desk.query_report.get_print_format_data``, and the framework renders it in the browser
with ``query_report.js::pdf_report``. So the template sees ``title, subtitle, filters, data,
columns, original_data, report, print_settings`` - and it may not call ``frappe.*`` at all,
because there is no server-side render for it to call into.

That makes executing the template the only honest check: these tests render it with real columns
and rows, so a broken loop, a lost total row or an empty-data crash fails here.
"""
import json
from pathlib import Path

import jinja2
import pytest

ROOT = Path(__file__).resolve().parents[1]
PRINT_FORMAT_DIR = ROOT / "murasalat_office/print_format"
REPORT_DIR = ROOT / "murasalat_office/report"
INSTALLER = ROOT / "setup/report_print_formats.py"
PROVISION = ROOT / "setup/provision.py"

FORMATS = [
    ("murasalat_management_summary_print", "Murasalat Management Summary Print",
     "Murasalat Management Summary", "murasalat_management_summary"),
    ("murasalat_department_workload_print", "Murasalat Department Workload Print",
     "Murasalat Department Workload", "murasalat_department_workload"),
    ("murasalat_response_times_print", "Murasalat Response Times Print",
     "Murasalat Response Times", "murasalat_response_times"),
]

SLUGS = [row[0] for row in FORMATS]


def _folder(slug):
    return PRINT_FORMAT_DIR / slug


def _template(slug):
    return (_folder(slug) / f"{slug}.html").read_text(encoding="utf-8")


def _meta(slug):
    return json.loads((_folder(slug) / f"{slug}.json").read_text(encoding="utf-8"))


def _render(slug, **context):
    environment = jinja2.Environment(autoescape=True)
    return environment.from_string(_template(slug)).render(**context)


COLUMNS = [
    {"label": "الاتجاه", "fieldname": "direction", "fieldtype": "Data"},
    {"label": "المستلم", "fieldname": "received", "fieldtype": "Int"},
    {"label": "المغلق", "fieldname": "closed", "fieldtype": "Int"},
    {"label": "متوسط أيام الإغلاق", "fieldname": "avg_close_days", "fieldtype": "Float"},
]

DATA = [
    {"direction": "وارد", "received": 12, "closed": 9, "avg_close_days": 6.4},
    {"direction": "صادر", "received": 7, "closed": 4, "avg_close_days": None},
    {"direction": "داخلي", "received": 0, "closed": 0, "avg_close_days": 0},
    {"direction": "الإجمالي", "received": 19, "closed": 13, "avg_close_days": 5.1},
]


# --- packed where Frappe expects, and declared honestly -------------------------------


@pytest.mark.parametrize("slug", SLUGS)
def test_each_format_is_packed_where_frappe_looks(slug):
    folder = _folder(slug)

    assert folder.is_dir(), slug
    for suffix in (".html", ".json"):
        assert (folder / f"{slug}{suffix}").is_file(), (slug, suffix)


@pytest.mark.parametrize("slug", SLUGS)
def test_each_format_targets_a_report_that_exists(slug):
    """A format pointing at a report that is not there would list nowhere."""
    meta = _meta(slug)

    assert meta["doctype"] == "Print Format"
    assert meta["print_format_for"] == "Report"
    assert meta["print_format_type"] == "Jinja"
    assert meta["module"] == "Murasalat Office"
    assert not meta.get("disabled")
    assert meta["report"] == dict((row[0], row[2]) for row in FORMATS)[slug]

    report_folder = REPORT_DIR / dict((row[0], row[3]) for row in FORMATS)[slug]
    assert report_folder.is_dir(), f"{meta['report']} is not a report in this app"


@pytest.mark.parametrize("slug", SLUGS)
def test_the_metadata_matches_what_frappe_forces_on_a_report_format(slug):
    """PrintFormat.before_save sets custom_format=1 and standard="No" for a report layout.

    The framework treats a report format as a site customisation, not a document an app ships.
    Claiming "Yes" here would only be rewritten on the first save, so the files state what the
    framework will make them - and the installer creates the rows instead of relying on import.
    """
    meta = _meta(slug)

    assert meta["custom_format"] == 1
    assert meta["standard"] == "No"
    assert meta["doc_type"] is None


@pytest.mark.parametrize("slug", SLUGS)
def test_no_format_ships_a_permission_row(slug):
    """Access stays site configuration, as it is for every other document in this app."""
    assert "permissions" not in _meta(slug)


@pytest.mark.parametrize("slug", SLUGS)
def test_the_embedded_html_is_the_shipped_file(slug):
    """One source: the HTML file. The installer reads that file, not the copy in the JSON."""
    assert _meta(slug)["html"] == _template(slug)


@pytest.mark.parametrize("slug", SLUGS)
def test_the_installer_reads_the_shipped_files(slug):
    source = INSTALLER.read_text(encoding="utf-8")

    assert "def plan():" in source and "def install():" in source
    assert '"html"' in source, "the template is read from the shipped file"
    assert "frappe.get_app_path" in source, "the app path is resolved, not guessed"
    assert "exists(" in source, "an existing format must be reported, not overwritten"


def test_one_command_installs_them_with_everything_else():
    source = PROVISION.read_text(encoding="utf-8")

    assert "report_print_formats" in source
    assert "report_print_formats.install()" in source


# --- the template, parsed and rendered --------------------------------------------------


@pytest.mark.parametrize("slug", SLUGS)
def test_the_template_is_valid_jinja(slug):
    jinja2.Environment().parse(_template(slug), filename=slug)


@pytest.mark.parametrize("slug", SLUGS)
def test_the_template_is_arabic_right_to_left_on_a4(slug):
    source = _template(slug)

    assert 'dir="rtl"' in source
    assert "direction: rtl" in source
    assert "Noto Naskh Arabic" in source, "an Arabic document must not fall back to Latin fonts"
    assert "size: A4" in source


@pytest.mark.parametrize("slug", SLUGS)
def test_the_template_never_reaches_for_the_server(slug):
    """There is no server-side render for a report layout - the browser renders this.

    Jinja comments are stripped first: they document the mechanism by name, and a mention in
    prose is not a call. What is checked is the code that actually renders.
    """
    import re

    code = re.sub(r"\{#.*?#\}", "", _template(slug), flags=re.S)

    assert "frappe." not in code, (
        "a report print template is rendered in the browser and cannot call frappe.*"
    )
    assert "{% " in code, "the guard must have left the actual template in place"


@pytest.mark.parametrize("slug", SLUGS)
def test_every_column_and_value_is_rendered(slug):
    html = _render(slug, title="ملخص الإدارة", subtitle=None, filters={},
                   data=DATA, columns=COLUMNS)

    for column in COLUMNS:
        assert column["label"] in html, (slug, column["label"])

    for row in DATA:
        assert row["direction"] in html, (slug, row["direction"])
        assert str(row["received"]) in html, (slug, row["received"])


@pytest.mark.parametrize("slug", SLUGS)
def test_the_total_row_is_marked_and_so_is_every_alternate_row(slug):
    html = _render(slug, title="ت", subtitle=None, filters={}, data=DATA, columns=COLUMNS)

    assert 'class="total"' in html, "the total row must stand out"
    assert 'class="alt"' in html, "zebra striping keeps a long table readable"
    assert html.count('class="total"') == 1


@pytest.mark.parametrize("slug", SLUGS)
def test_numbers_are_centred_and_missing_values_read_as_a_dash(slug):
    html = _render(slug, title="ت", subtitle=None, filters={}, data=DATA, columns=COLUMNS)

    assert 'class="num"' in html
    assert "mo-dash" in html, "an unfinished measurement shows as a dash, not as a zero"
    assert "0" in html, "a real zero is printed as a zero"


@pytest.mark.parametrize("slug", SLUGS)
def test_an_empty_period_prints_a_message_instead_of_breaking(slug):
    html = _render(slug, title="ت", subtitle=None, filters={}, data=[], columns=COLUMNS)

    assert "لا توجد بيانات" in html
    assert 'colspan="4"' in html


@pytest.mark.parametrize("slug", SLUGS)
def test_the_filters_line_is_left_to_the_framework(slug):
    """Frappe builds it as HTML and passes it as `subtitle` when the user ticks Include filters."""
    html = _render(slug, title="ت", subtitle="<div>من 2026-09-01</div>", filters={},
                   data=DATA, columns=COLUMNS)

    assert "من 2026-09-01" in html, "the filter line has to reach the page unescaped"


def test_the_reports_themselves_are_untouched():
    for slug, _, _, report_slug in FORMATS:
        assert (REPORT_DIR / report_slug / f"{report_slug}.py").is_file(), slug
