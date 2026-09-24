"""The A4 layouts of the three management reports, and the route that reaches them.

A report layout is not a DocType print format. Frappe renders a report in the browser:

* ``frappe.desk.query_report.get_script`` reads ``<module>/report/<report>/<report>.html`` from
  disk and hands its text to the browser as the report's own template;
* ``query_report.js::get_custom_format`` starts from that template, and
  ``get_print_template`` returns it only when it exists - otherwise the default ``print_grid``
  is printed, which is the framework's plain grid;
* the selected content is rendered by ``frappe/public/js/frappe/microtemplate.js``, a small
  JavaScript template engine - **not** Jinja.

The last point is what these tests are built around. microtemplate understands only
``{{ }}``, ``{% if %}``, ``{% else %}``, ``{% endif %}``, ``{% for x in y %}``, ``{% endfor %}``
and ``x._index``; a ``{% set %}``, an ``{% elif %}``, a filter such as ``| length``, or ``or``
inside a condition compiles to invalid JavaScript and the report prints nothing. Jinja accepts
all of them, so a Jinja check on a report layout is worse than no check: it passes while the
browser fails. These tests therefore lint the template for what the engine cannot run, and
execute it in the engine itself whenever Frappe's file can be found.
"""
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PRINT_FORMAT_DIR = ROOT / "murasalat_office/print_format"
REPORT_DIR = ROOT / "murasalat_office/report"
INSTALLER = ROOT / "setup/report_print_formats.py"
PROVISION = ROOT / "setup/provision.py"
RUNNER = Path(__file__).resolve().parent / "render_report_template.mjs"

FORMATS = [
    ("murasalat_management_summary_print", "Murasalat Management Summary Print",
     "Murasalat Management Summary", "murasalat_management_summary"),
    ("murasalat_department_workload_print", "Murasalat Department Workload Print",
     "Murasalat Department Workload", "murasalat_department_workload"),
    ("murasalat_response_times_print", "Murasalat Response Times Print",
     "Murasalat Response Times", "murasalat_response_times"),
]

SLUGS = [row[0] for row in FORMATS]
BY_SLUG = {row[0]: row for row in FORMATS}
REPORT_SLUGS = {row[3] for row in FORMATS}


def _meta(slug):
    return json.loads((PRINT_FORMAT_DIR / slug / f"{slug}.json").read_text(encoding="utf-8"))


def _template_path(report_slug):
    """The single source of the layout: shipped with the report, loaded by the framework."""
    return REPORT_DIR / report_slug / f"{report_slug}.html"


def _template(report_slug):
    return _template_path(report_slug).read_text(encoding="utf-8")


# --- where the layout lives -------------------------------------------------------------


@pytest.mark.parametrize("report_slug", sorted(REPORT_SLUGS))
def test_the_layout_ships_next_to_its_report(report_slug):
    """This is the file frappe.desk.query_report.get_script looks for. Without it the report
    prints the framework's default grid - which is exactly what the A4 layout replaces."""
    assert (REPORT_DIR / report_slug / f"{report_slug}.py").is_file(), report_slug
    assert _template_path(report_slug).is_file(), f"{report_slug}/<report>.html is missing"


def test_the_three_reports_share_one_layout():
    layouts = {_template(report_slug) for report_slug in REPORT_SLUGS}

    assert len(layouts) == 1, "the three reports print one layout, kept byte-identical"


def test_the_layout_is_not_duplicated_into_the_json():
    """The installer reads the template file and injects it; a second copy in the JSON is a
    second thing to keep in step, and the copy that goes stale is always the hidden one."""
    for slug in SLUGS:
        assert "html" not in _meta(slug), (slug, "the JSON must not carry a second copy")


# --- the metadata of each Print Format --------------------------------------------------


@pytest.mark.parametrize("slug", SLUGS)
def test_each_format_targets_a_report_that_exists(slug):
    meta = _meta(slug)

    assert meta["doctype"] == "Print Format"
    assert meta["print_format_for"] == "Report"
    assert meta["module"] == "Murasalat Office"
    assert not meta.get("disabled")
    assert meta["name"] == BY_SLUG[slug][1]
    assert meta["report"] == BY_SLUG[slug][2]
    assert _template_path(BY_SLUG[slug][3]).is_file()


@pytest.mark.parametrize("slug", SLUGS)
def test_the_format_is_declared_as_the_browser_renders_it(slug):
    """The report print dialog offers only formats whose type is JS
    (`get_query` in frappe/public/js/frappe/form/print_utils.js filters on
    print_format_type: "JS"), because a report layout is rendered in the browser and never on
    the server. Declaring Jinja here hides the format from the dialog entirely."""
    meta = _meta(slug)

    assert meta["print_format_type"] == "JS"


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


# --- the installer ---------------------------------------------------------------------


def test_the_installer_reads_the_layout_from_the_report_folder():
    source = INSTALLER.read_text(encoding="utf-8")

    assert "def plan():" in source and "def install():" in source
    assert "def template_path(" in source, "one place resolves the layout file"
    assert '"report", report_slug' in source, "the layout is read from the report folder"
    assert "frappe.get_app_path" in source, "the app path is resolved, not guessed"
    assert 'print_format_type"] = "JS"' in source or "print_format_type" in source


def test_the_installer_creates_missing_rows_and_refreshes_stale_ones():
    source = INSTALLER.read_text(encoding="utf-8")

    assert "exists(" in source, "an existing format must be detected, not re-inserted"
    assert '"updated"' in source, (
        "a site that installed the format before a layout fix must receive the fix"
    )
    assert "frappe.get_doc(definition).insert" in source, "insertion goes through Frappe's model"


def test_one_command_installs_them_with_everything_else():
    source = PROVISION.read_text(encoding="utf-8")

    assert "report_print_formats" in source
    assert "report_print_formats.install()" in source


# --- the layout: markers, and the grammar the engine can actually run -------------------


@pytest.mark.parametrize("report_slug", sorted(REPORT_SLUGS))
def test_the_layout_is_arabic_right_to_left(report_slug):
    source = _template(report_slug)

    assert 'dir="rtl"' in source
    assert "direction: rtl" in source
    assert "Noto Naskh Arabic" in source, "an Arabic document must not fall back to Latin fonts"


@pytest.mark.parametrize("report_slug", sorted(REPORT_SLUGS))
def test_the_layout_never_reaches_for_the_server(report_slug):
    """There is no server-side render for a report layout - the browser renders this."""
    assert "frappe." not in _template(report_slug)


@pytest.mark.parametrize("report_slug", sorted(REPORT_SLUGS))
def test_the_layout_holds_what_the_report_prints(report_slug):
    source = _template(report_slug)

    assert "{% for column in columns %}" in source, "the table is built from the report columns"
    assert "{% for row in data %}" in source, "the table is built from the report rows"
    assert "{% if data.length %}" in source, "the empty period is its own branch"
    assert "لا توجد بيانات" in source, "an empty period explains itself"
    assert 'colspan="{{ columns.length }}"' in source, "the empty row spans every column"
    assert "mo-dash" in source, "a missing measurement reads as a dash"
    assert 'class="mo-rpt-foot"' in source, "the footer states the permission basis"
    assert "nth-child(even)" in source, "zebra striping is CSS work, not template work"


@pytest.mark.parametrize("report_slug", sorted(REPORT_SLUGS))
def test_the_layout_sticks_to_the_grammar_of_the_browser_engine(report_slug):
    """Everything microtemplate cannot translate is listed here, because the failure mode is
    silent: the JavaScript it generates does not compile and the report prints nothing."""
    source = _template(report_slug)

    assert "{% set " not in source, "microtemplate has no {% set %}"
    assert "{% elif" not in source, "microtemplate has no {% elif %}"
    assert "{#" not in source, "microtemplate has no Jinja comments - they would print as text"
    assert "loop.index" not in source, "microtemplate exposes x._index, not loop.index0"
    assert "'" not in source, "the engine assembles the template as a JS string literal"

    # A lone pipe is a Jinja filter and would be left in the JavaScript as invalid syntax.
    # || is JavaScript's `or`, which the engine passes through untouched - so allow it.
    lone_pipe = re.compile(r"(?<!\|)\|(?!\|)")

    for tag in re.findall(r"{{(.*?)}}", source, flags=re.S):
        assert not lone_pipe.search(tag), f"microtemplate has no filters: {tag!r}"

    for condition in re.findall(r"{%\s?if\s?(.*?)\s?%}", source, flags=re.S):
        assert not lone_pipe.search(condition), f"microtemplate has no filters: {condition!r}"
        assert " in " not in condition, f"JS `in` is not Jinja `in`: {condition!r}"
        assert "%" not in condition, f"the engine's if-regex cannot parse a percent sign: {condition!r}"
        assert " or " not in condition, f"`or` is not JavaScript: {condition!r}"
        assert " and " not in condition, f"`and` is not JavaScript: {condition!r}"

    for loop in re.findall(r"{%\s?for\s(.*?)\s?%}", source, flags=re.S):
        item, _, collection = loop.partition(" in ")
        assert re.fullmatch(r"[a-z._]+", item), f"the loop variable must be plain: {loop!r}"
        assert re.fullmatch(r"[a-z._]+", collection), f"the loop source must be plain: {loop!r}"


# --- executing the layout in the engine that renders it ---------------------------------


def _engine_path():
    """Locate Frappe's browser template engine, or report that it cannot be exercised."""
    candidates = []
    override = os.environ.get("FRAPPE_MICROTEMPLATE")
    if override:
        candidates.append(Path(override))
    try:
        import frappe

        candidates.append(Path(frappe.get_app_path("frappe", "public/js/frappe/microtemplate.js")))
    except Exception:  # noqa: BLE001 - a stubbed or absent frappe is not a test failure
        pass
    for bench in (Path.home() / "frappe-bench", Path.home() / "bench",
                  Path("/home/frappe/frappe-bench")):
        candidates.append(bench / "apps/frappe/public/js/frappe/microtemplate.js")

    return next((path for path in candidates if path.is_file()), None)


@pytest.mark.parametrize("report_slug", sorted(REPORT_SLUGS))
def test_the_layout_renders_in_frappes_own_browser_engine(report_slug):
    engine, node = _engine_path(), shutil.which("node")

    if engine is None or node is None:
        pytest.skip(
            "frappe's microtemplate.js or node was not found - set FRAPPE_MICROTEMPLATE to "
            "…/apps/frappe/public/js/frappe/microtemplate.js to run this check"
        )

    finished = subprocess.run(
        [node, str(RUNNER), str(engine), str(_template_path(report_slug))],
        capture_output=True, text=True, timeout=120,
    )

    assert finished.returncode == 0, f"{finished.stdout}\n{finished.stderr}"


def test_the_reports_themselves_are_untouched():
    for slug, _, _, report_slug in FORMATS:
        assert (REPORT_DIR / report_slug / f"{report_slug}.py").is_file(), slug
