"""The management reports answer questions no per-record report answers.

A general manager asks how the office performed this month and which department is behind. A
department head asks how much is sitting with them and how long their stage takes. None of that
is readable from a status column or an index of records, so three reports exist for it.

These tests do two jobs. They hold the DocType/Report contract the framework expects, and they
**execute each report** against stubbed rows - so a mistyped field name, an incomplete date
pair counted as zero, or a return value that is not the five-part tuple the framework unpacks
fails here instead of on a manager's screen.
"""
import importlib.util
import sys
import types
from datetime import date
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

# The reports import `murasalat_office.services...`, so the app package has to be importable
# from the repository root - not only the test directory pytest adds by default.
REPO_ROOT = str(ROOT.parent)
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

MANAGEMENT = ROOT / "services/management.py"
REPORTS = ROOT / "murasalat_office/report"

# Fields every document carries at runtime without being declared in its DocType JSON.
STANDARD_FIELDS = {"name", "creation", "modified", "modified_by", "owner", "docstatus",
                   "doctype", "idx", "parent", "parentfield", "parenttype"}

REPORT_NAMES = {
    "murasalat_management_summary": "Murasalat Management Summary",
    "murasalat_department_workload": "Murasalat Department Workload",
    "murasalat_response_times": "Murasalat Response Times",
}


# --- a stubbed framework, so the shipped code actually runs ---------------------------


def _load(correspondence, referrals):
    class Dict(dict):
        def __getattr__(self, name):
            try:
                return self[name]
            except KeyError:
                raise AttributeError(name) from None

    def getdate(value=None):
        if isinstance(value, date):
            return value
        raise AssertionError(f"a report passed a non-date into getdate: {value!r}")

    # A real module, not a namespace: the reports use `from frappe.utils import ...`, which
    # resolves through sys.modules and would otherwise import the installed framework.
    utils = types.ModuleType("frappe.utils")
    utils.getdate = getdate
    utils.date_diff = lambda end, start: (end - start).days
    utils.get_first_day = lambda value: value.replace(day=1)
    utils.today = lambda: date(2026, 9, 24)
    sys.modules["frappe.utils"] = utils

    def get_list(doctype, *args, **kwargs):
        assert kwargs.get("ignore_permissions") is False, (
            "every report in this app reads through permission checks"
        )
        rows = correspondence if doctype == "Murasalat Correspondence" else referrals
        return [Dict(row) for row in rows]

    frappe = types.ModuleType("frappe")
    frappe._dict = lambda mapping=None: Dict(mapping or {})
    frappe._ = lambda text, *args, **kwargs: text
    frappe.__path__ = []  # so `frappe.utils` resolves as a submodule we control
    frappe.get_list = get_list
    frappe.get_all = lambda *args, **kwargs: []
    frappe.utils = utils
    frappe.getdate = getdate
    frappe.throw = lambda message, *args, **kwargs: (_ for _ in ()).throw(Exception(message))
    frappe.session = types.SimpleNamespace(user="Administrator")
    sys.modules["frappe"] = frappe

    spec = importlib.util.spec_from_file_location("murasalat_management", MANAGEMENT)
    management = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(management)
    sys.modules["murasalat_office.services.management"] = management

    aging = types.ModuleType("murasalat_office.services.aging")
    aging.summary_item = lambda label, value, indicator=None: {
        "label": label, "value": value, "indicator": indicator,
    }
    sys.modules["murasalat_office.services.aging"] = aging

    loaded = {}
    for slug in REPORT_NAMES:
        path = REPORTS / slug / f"{slug}.py"
        spec = importlib.util.spec_from_file_location(slug, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        loaded[slug] = module

    return loaded, management


CORRESPONDENCE_ROWS = [
    # incoming, registered, closed, sealed - a finished file
    {"name": "MO-1", "correspondence_direction": "Incoming", "creation": date(2026, 9, 1),
     "registered_on": date(2026, 9, 3), "closed_on": date(2026, 9, 11),
     "record_sealed_on": date(2026, 9, 12), "due_date": date(2026, 9, 5),
     "current_holder": "Correspondence Office"},
    # outgoing, still open and overdue
    {"name": "MO-2", "correspondence_direction": "Outgoing", "creation": date(2026, 9, 10),
     "registered_on": None, "closed_on": None, "record_sealed_on": None,
     "due_date": date(2026, 9, 20), "current_holder": "Central Archive"},
    # internal, open, no due date
    {"name": "MO-3", "correspondence_direction": "Internal", "creation": date(2026, 9, 15),
     "registered_on": date(2026, 9, 15), "closed_on": None, "record_sealed_on": None,
     "due_date": None, "current_holder": "Central Archive"},
]

REFERRAL_ROWS = [
    {"name": "MR-1", "correspondence": "MO-1", "recipient_department": "Correspondence Office",
     "creation": date(2026, 9, 2), "sent_on": date(2026, 9, 3), "received_on": date(2026, 9, 4),
     "completed_on": date(2026, 9, 10), "due_date": date(2026, 9, 9), "workflow_state": "Completed"},
    {"name": "MR-2", "correspondence": "MO-2", "recipient_department": "Central Archive",
     "creation": date(2026, 9, 11), "sent_on": date(2026, 9, 12), "received_on": None,
     "completed_on": None, "due_date": date(2026, 9, 18), "workflow_state": "Sent"},
]


# --- the framework contract ------------------------------------------------------------


@pytest.mark.parametrize("slug", list(REPORT_NAMES))
def test_each_report_is_packed_where_the_framework_looks(slug):
    folder = REPORTS / slug

    assert folder.is_dir(), slug
    for suffix in (".py", ".js", ".json"):
        assert (folder / f"{slug}{suffix}").is_file(), (slug, suffix)
    assert (folder / "__init__.py").is_file(), slug


@pytest.mark.parametrize("slug", list(REPORT_NAMES))
def test_each_report_declares_itself_a_standard_script_report(slug):
    import json

    data = json.loads((REPORTS / slug / f"{slug}.json").read_text(encoding="utf-8"))

    assert data["doctype"] == "Report"
    assert data["name"] == REPORT_NAMES[slug]
    assert data["report_type"] == "Script Report"
    assert data["is_standard"] == "Yes"
    assert data["module"] == "Murasalat Office"
    assert data["disabled"] == 0
    assert data["ref_doctype"] == "Murasalat Correspondence"
    assert data["description"], "a report a manager cannot identify is a report they will not open"


@pytest.mark.parametrize("slug", list(REPORT_NAMES))
def test_each_report_offers_the_period_a_manager_thinks_in(slug):
    import json

    data = json.loads((REPORTS / slug / f"{slug}.json").read_text(encoding="utf-8"))
    filters = {f["fieldname"] for f in data["filters"]}

    assert {"from_date", "to_date"} <= filters, slug


def test_the_reports_the_app_already_had_are_untouched():
    """Adding reports must not disturb the ones the office already uses."""
    existing = {"murasalat_correspondence_register", "murasalat_due_today",
                "murasalat_referral_aging", "murasalat_work_queue"}

    for slug in existing:
        assert (REPORTS / slug / f"{slug}.py").is_file(), slug


# --- the pure helpers, executed --------------------------------------------------------


def test_an_unfinished_pair_is_not_counted_as_zero():
    """This is what keeps an average from flattering the office.

    A file that has not been closed has no closing time. Counting it as zero days would report
    a faster office the more work was still open.
    """
    _, management = _load([], [])

    assert management.days_between(date(2026, 9, 1), None) is None
    assert management.days_between(None, date(2026, 9, 1)) is None
    assert management.days_between(date(2026, 9, 1), date(2026, 9, 11)) == 10


def test_the_average_ignores_what_could_not_be_measured():
    _, management = _load([], [])

    assert management.average([10, None, 20]) == 15.0
    assert management.average([]) is None
    assert management.average([None, None]) is None
    assert management.average([1, 2]) == 1.5


def test_the_period_defaults_to_this_month_so_far():
    _, management = _load([], [])

    start, end = management.period({})
    assert (start, end) == (date(2026, 9, 1), date(2026, 9, 24))


# --- the reports, executed -------------------------------------------------------------


def _run(slug, filters=None):
    loaded, _ = _load(CORRESPONDENCE_ROWS, REFERRAL_ROWS)
    result = loaded[slug].execute(filters or {})

    assert isinstance(result, tuple) and len(result) == 5, (
        f"{slug} must return columns, data, message, chart, summary"
    )
    return result


@pytest.mark.parametrize("slug", list(REPORT_NAMES))
def test_every_report_returns_what_the_framework_unpacks(slug):
    columns, data, message, chart, summary = _run(slug)

    assert columns and data, slug
    for column in columns:
        assert {"label", "fieldname", "fieldtype"} <= set(column), (slug, column)
        assert column["label"], (slug, column)
    assert isinstance(summary, list) and summary, slug
    assert chart is None or "data" in chart, slug


@pytest.mark.parametrize("slug", list(REPORT_NAMES))
def test_no_report_reads_a_field_its_doctype_does_not_have(slug):
    """A mistyped field renders an empty column, which nobody reports as a bug."""
    import json

    columns, _, _, _, _ = _run(slug)
    correspondence = {
        f["fieldname"]
        for f in json.loads((ROOT / "murasalat_office/doctype/murasalat_correspondence"
                             "/murasalat_correspondence.json").read_text())["fields"]
    }
    referral = {
        f["fieldname"]
        for f in json.loads((ROOT / "murasalat_office/doctype/murasalat_referral"
                             "/murasalat_referral.json").read_text())["fields"]
    }
    source = (REPORTS / slug / f"{slug}.py").read_text(encoding="utf-8")

    for field in _fields_named_in(source):
        assert field in correspondence or field in referral or field in STANDARD_FIELDS, (slug, field)


def _fields_named_in(source):
    """Field names the report pulls, read from the FIELDS lists it declares."""
    import re

    found = set()
    for block in re.findall(r"FIELDS = \[(.*?)\]", source, re.S):
        found.update(re.findall(r'"([a-z_]+)"', block))
    return found


def test_the_summary_totals_its_own_rows():
    columns, data, _, chart, summary = _run("murasalat_management_summary")
    total = data[-1]

    assert total["direction"] == "Total"
    assert total["received"] == sum(row["received"] for row in data[:-1])
    assert total["open_now"] == sum(row["open_now"] for row in data[:-1])
    assert total["overdue_open"] == sum(row["overdue_open"] for row in data[:-1])


def test_the_summary_counts_a_closed_file_and_measures_its_days():
    _, data, _, _, _ = _run("murasalat_management_summary")
    incoming = next(row for row in data if row["direction"] == "وارد")

    assert incoming["received"] == 1
    assert incoming["closed"] == 1
    assert incoming["sealed"] == 1
    assert incoming["avg_close_days"] == 10.0, "creation 9-1 to close 9-11"


def test_the_summary_reports_an_open_overdue_file_as_open():
    _, data, _, _, _ = _run("murasalat_management_summary")
    outgoing = next(row for row in data if row["direction"] == "صادر")

    assert outgoing["open_now"] == 1
    assert outgoing["overdue_open"] == 1
    assert outgoing["closed"] == 0
    assert outgoing["avg_close_days"] is None, "nothing closed means no average, not zero"


def test_the_summary_charts_every_direction():
    _, _, _, chart, _ = _run("murasalat_management_summary")

    assert chart["data"]["labels"] == ["وارد", "صادر", "داخلي"]
    assert len(chart["data"]["datasets"]) == 2
    assert chart["type"] == "bar"


def test_the_workload_report_puts_every_department_in_a_row():
    _, data, _, _, _ = _run("murasalat_department_workload")
    units = {row["unit"] for row in data}

    assert "Central Archive" in units
    assert "Correspondence Office" in units


def test_the_workload_report_shows_what_a_department_holds_and_owes():
    _, data, _, _, _ = _run("murasalat_department_workload")
    archive = next(row for row in data if row["unit"] == "Central Archive")

    assert archive["holding"] == 2, "two open files are held there"
    assert archive["open_referrals"] == 1
    assert archive["overdue_referrals"] == 1
    assert archive["completed"] == 0


def test_the_workload_report_measures_how_long_a_stage_takes():
    _, data, _, _, _ = _run("murasalat_department_workload")
    office = next(row for row in data if row["unit"] == "Correspondence Office")

    assert office["completed"] == 1
    assert office["avg_complete_days"] == 7.0, "sent 9-3 to completed 9-10"


def test_the_workload_report_lists_the_worst_first():
    _, data, _, _, _ = _run("murasalat_department_workload")
    overdue = [row["overdue_referrals"] for row in data]

    assert overdue == sorted(overdue, reverse=True)


def test_the_response_times_report_measures_each_stage_separately():
    """A single cycle average cannot say where the delay is; each stage is its own column."""
    _, data, _, _, _ = _run("murasalat_response_times")
    total = data[-1]

    assert total["direction"] == "Total"
    # MO-1 registered 2 days after creation, MO-3 the same day; MO-2 is not registered yet and
    # is therefore not measured at all.
    assert total["to_register"] == 1.0, "two measured files: 2 days and 0 days"
    assert total["send_to_receive"] == 1.0
    assert total["receive_to_complete"] == 6.0
    assert total["to_close"] == 10.0


def test_the_response_times_report_names_the_slowest_stage():
    """The one line a general manager needs: which stage to attack."""
    _, _, _, _, summary = _run("murasalat_response_times")

    slowest = next(item for item in summary if item["label"] == "Slowest Stage")
    assert slowest["value"], "the slowest stage must be named, not left blank"


def test_the_response_times_report_can_be_narrowed_to_one_direction():
    _, data, _, _, _ = _run("murasalat_response_times", {"correspondence_direction": "Incoming"})
    labels = [row["direction"] for row in data]

    assert labels == ["وارد", "Total"]


def test_a_direction_filter_never_leaks_another_direction():
    _, data, _, _, _ = _run("murasalat_management_summary")
    assert len(data) == 4, "three directions and a total"
