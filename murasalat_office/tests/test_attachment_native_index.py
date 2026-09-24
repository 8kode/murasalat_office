"""Attachments are indexed from the framework's own File document.

Frappe has exactly one way to attach a file to a document: a ``File`` row carrying
``attached_to_doctype`` and ``attached_to_name``. The sidebar panel, drag-and-drop, the REST
upload endpoint and a row's own Attach control all go through it. The app registers two
``File`` events in ``hooks.py``, and these tests drive them against a stubbed ``frappe`` - so
the decision they make, file this upload in the table or leave it to the row the user is
filling, is executed rather than inspected.

``attached_to_field`` is the signal. ``frappe/client.py::attach_file`` sets it from the
``docfield`` argument, so it is empty for an upload aimed at the record and carries the field
name when the user uploaded into a specific field.
"""
import importlib.util
import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SERVICE = ROOT / "services/attachment_index.py"
HOOKS = ROOT / "hooks.py"
PATCHES = ROOT / "patches.txt"

CORRESPONDENCE = "Murasalat Correspondence"
REFERRAL = "Murasalat Referral"
TABLE = "Murasalat Attachment"


class Refused(Exception):
    """Stands in for frappe.throw, which raises rather than returns."""


class Record:
    def __init__(self, name):
        self.name = name
        self.attachments = []
        self.saved = 0

    def append(self, fieldname, row):
        assert fieldname == "attachments", fieldname
        self.attachments.append(types.SimpleNamespace(name="att-row-%d" % len(self.attachments), **row))

    def save(self):
        self.saved += 1


def load(**behaviour):
    """Import the service against a stubbed frappe, and return it with its call log."""
    log = {"loaded": [], "queries": [], "thrown": [], "errors": []}

    frappe = types.ModuleType("frappe")
    frappe._ = lambda text, *args, **kwargs: text

    def throw(message, *args, **kwargs):
        log["thrown"].append(message)
        raise Refused(message)

    def get_value(doctype, *args, **kwargs):
        log["queries"].append(doctype)
        if doctype == TABLE:  # the duplicate-row probe
            return behaviour.get("row_exists")
        return behaviour.get("sealed")  # the seal lookup

    def get_all(*args, **kwargs):
        target = args[0] if args else kwargs.get("doctype")
        if target == "File":
            wanted = (kwargs.get("filters") or {}).get("attached_to_doctype")
            return [row for row in behaviour.get("files", []) if row["attached_to_doctype"] == wanted]
        return behaviour.get("sealed_names", {}).get(target, [])

    def get_doc(doctype, name=None):
        log["loaded"].append((doctype, name))
        factory = behaviour.get("get_doc")
        if factory is None:
            raise AssertionError("the service loaded %s %s when it should not have" % (doctype, name))
        return factory(doctype, name)

    frappe.throw = throw
    frappe.get_doc = get_doc
    frappe.get_all = get_all
    def log_error(*args, **kwargs):
        log["errors"].append(kwargs.get("title") or (args[0] if args else None))

    frappe.log_error = log_error
    frappe.get_traceback = lambda: ""
    frappe.db = types.SimpleNamespace(
        get_value=get_value,
        exists=behaviour.get("exists", lambda *args, **kwargs: True),
        commit=lambda: None,
    )

    sys.modules["frappe"] = frappe
    spec = importlib.util.spec_from_file_location("murasalat_attachment_index", SERVICE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, log


def upload(doctype, name, field=None, url="/files/a.pdf", file_name="a.pdf"):
    return types.SimpleNamespace(
        attached_to_doctype=doctype,
        attached_to_name=name,
        attached_to_field=field,
        file_url=url,
        file_name=file_name,
    )


# --- which uploads are ours to file --------------------------------------------


def test_only_record_level_uploads_are_indexed():
    module, _ = load()

    assert module.should_index(CORRESPONDENCE, None) is True
    assert module.should_index(REFERRAL, None) is True
    assert module.should_index(CORRESPONDENCE, "") is True
    assert module.should_index(CORRESPONDENCE, "file") is False, "a row's own Attach control"
    assert module.should_index("File", None) is False
    assert module.should_index("Sales Invoice", None) is False


def test_a_field_scoped_upload_is_left_to_the_row_being_filled():
    module, log = load()
    module.index_file_in_the_record(upload(CORRESPONDENCE, "MC-1", field="file"))

    assert log["loaded"] == [], "a field upload must not produce a second row"


def test_a_record_level_upload_becomes_a_row():
    record = Record("MC-2026-0001")
    module, log = load(get_doc=lambda dtype, name: record)
    module.index_file_in_the_record(upload(CORRESPONDENCE, "MC-2026-0001"))

    assert record.saved == 1, "the row is written through the controller, not the table"
    assert record.attachments[0].file == "/files/a.pdf"
    assert record.attachments[0].attachment_type == "Attachment"
    assert log["loaded"] == [(CORRESPONDENCE, "MC-2026-0001")]


def test_a_file_already_in_the_table_is_not_filed_twice():
    module, log = load(row_exists="att-row-1")
    module.index_file_in_the_record(upload(CORRESPONDENCE, "MC-1"))

    assert log["loaded"] == []


def test_a_file_attached_to_a_record_that_is_gone_is_ignored():
    module, log = load(exists=lambda *args, **kwargs: False)
    module.index_file_in_the_record(upload(CORRESPONDENCE, "MC-gone"))

    assert log["loaded"] == []


def test_a_referral_upload_is_filed_too():
    record = Record("REF-1")
    module, _ = load(get_doc=lambda dtype, name: record)
    module.index_file_in_the_record(upload(REFERRAL, "REF-1"))

    assert record.saved == 1


# --- the seal is enforced by the framework, not by hiding a button --------------


def test_a_sealed_record_refuses_the_file_before_it_is_stored():
    module, log = load(sealed="2026-01-01 10:00:00")

    with pytest.raises(Refused):
        module.refuse_file_on_a_sealed_record(upload(CORRESPONDENCE, "MC-1"))

    assert log["thrown"], "the refusal has to carry a message"


def test_an_unsealed_record_is_not_refused():
    module, log = load(sealed=None)
    module.refuse_file_on_a_sealed_record(upload(CORRESPONDENCE, "MC-1"))

    assert log["thrown"] == []


def test_only_the_correspondence_is_sealed_so_the_referral_guard_does_nothing():
    module, log = load(sealed="2026-01-01 10:00:00")
    module.refuse_file_on_a_sealed_record(upload(REFERRAL, "REF-1"))

    assert REFERRAL not in module.SEALED_DOCTYPES
    assert module.SEALED_DOCTYPES[CORRESPONDENCE] == "record_sealed_on"
    assert log["thrown"] == [], "a DocType with no seal column is never probed"
    assert log["queries"] == []


def test_an_unrelated_doctype_is_never_probed():
    module, log = load(sealed="2026-01-01 10:00:00")
    module.refuse_file_on_a_sealed_record(upload("Sales Invoice", "SINV-1"))
    module.index_file_in_the_record(upload("Sales Invoice", "SINV-1"))

    assert log["queries"] == []
    assert log["loaded"] == []


# --- the backfill -----------------------------------------------------------------


def files(*entries):
    """File rows as the service queries them: one DocType at a time."""
    return [
        {
            "attached_to_doctype": doctype,
            "attached_to_name": record,
            "attached_to_field": field,
            "file_url": url,
            "file_name": url.split("/")[-1],
        }
        for doctype, record, field, url in entries
    ]


def test_the_backfill_plans_a_row_for_a_file_that_has_none():
    module, _ = load(
        files=files(
            (CORRESPONDENCE, "MC-1", None, "/files/a.pdf"),
            (CORRESPONDENCE, "MC-1", "file", "/files/typed.pdf"),
        ),
    )
    plan = module.plan_indexing()

    assert [entry["file"] for entry in plan["create"]] == ["/files/a.pdf"]
    assert [entry["file"] for entry in plan["sealed"]] == [], "nothing is sealed here"


def test_the_backfill_leaves_a_sealed_record_alone():
    """A sealed record's stored hash covers its rows - writing one would break its seal."""
    module, _ = load(
        files=files(
            (CORRESPONDENCE, "MC-1", None, "/files/a.pdf"),
            (CORRESPONDENCE, "MC-2", None, "/files/b.pdf"),
        ),
        sealed_names={CORRESPONDENCE: ["MC-1"]},
    )
    plan = module.plan_indexing()

    assert [entry["record"] for entry in plan["create"]] == ["MC-2"]
    assert [entry["record"] for entry in plan["sealed"]] == ["MC-1"]


def test_the_backfill_skips_a_file_a_row_already_describes():
    module, _ = load(files=files((CORRESPONDENCE, "MC-1", None, "/files/a.pdf")), row_exists="att-row-9")
    plan = module.plan_indexing()

    assert plan["create"] == []
    assert len(plan["already_indexed"]) == 1


def test_the_backfill_reports_a_file_whose_record_is_gone():
    module, _ = load(files=files((CORRESPONDENCE, "MC-gone", None, "/files/a.pdf")),
        exists=lambda *args, **kwargs: False,
    )
    plan = module.plan_indexing()

    assert plan["create"] == []
    assert len(plan["orphaned"]) == 1


def test_a_plan_and_its_write_agree_on_what_to_create():
    record_a, record_b = Record("MC-1"), Record("MC-2")
    records = {"MC-1": record_a, "MC-2": record_b}
    module, _ = load(
        files=files(
            (CORRESPONDENCE, "MC-1", None, "/files/a.pdf"),
            (CORRESPONDENCE, "MC-2", None, "/files/b.pdf"),
        ),
        get_doc=lambda dtype, name: records[name],
    )
    plan = module.plan_indexing()
    summary = module.apply_indexing(plan)

    assert summary["created"] == 2
    assert summary["failed"] == 0
    assert [record.saved for record in records.values()] == [1, 1]


# --- the wiring -------------------------------------------------------------------


def test_hooks_register_the_native_file_events():
    hooks = HOOKS.read_text(encoding="utf-8")

    assert "doc_events = {" in hooks
    assert '"File": {' in hooks
    assert "murasalat_office.services.attachment_index.refuse_file_on_a_sealed_record" in hooks
    assert "murasalat_office.services.attachment_index.index_file_in_the_record" in hooks
    assert SERVICE.is_file()


def test_an_indexing_failure_does_not_abort_the_upload():
    """The file is already stored when this runs; losing it would be worse than a lost row."""
    def refuses(doctype, name):
        raise RuntimeError("the record refused the row")

    module, log = load(get_doc=refuses)

    module.index_file_in_the_record(upload(CORRESPONDENCE, "MC-1"))

    assert log["errors"] == ["Attachment index failed"], "the failure is recorded, not swallowed"


def test_the_backfill_is_declared_the_way_frappe_can_resolve_it():
    """A declaration that made `bench migrate` abort with NameError.

    patch_handler.execute_patch runs `exec(patch, globals())` for a line prefixed with
    `execute:`, so the dotted path is evaluated in patch_handler's own namespace - which holds
    no app name, only what that module imported. Its other branch resolves the line with
    frappe.get_attr, which imports the module properly. So the module path is listed bare.
    """
    patches = PATCHES.read_text(encoding="utf-8")
    line = "murasalat_office.patches.v0_23_index_record_attachments"

    assert line in patches
    assert "execute:" + line not in patches, "this form aborts migrate with NameError"

    module = ROOT / "patches/v0_23_index_record_attachments.py"
    assert module.is_file()
    assert "def execute():" in module.read_text(encoding="utf-8")


def test_the_patch_describes_itself_while_migrating():
    """Frappe prints the patch function's docstring, so it must say what the patch does."""
    module = (ROOT / "patches/v0_23_index_record_attachments.py").read_text(encoding="utf-8")
    after_def = module.split("def execute():", 1)[1].strip()

    assert after_def.startswith('"""'), "migrate would print an empty description"


def test_the_patch_tells_the_operator_what_it_did():
    source = (ROOT / "patches/v0_23_index_record_attachments.py").read_text(encoding="utf-8")

    assert "plan_indexing()" in source, "the plan is printed before anything is written"
    assert "skipped_sealed" in source
