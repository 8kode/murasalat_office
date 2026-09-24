"""Contract tests for the attachment rules.

The attachment table is a child table, so its rules are metadata plus the shared validator
in ``services/records.py``. What is pinned here is the policy an archive depends on:
a controlled vocabulary instead of an invented folder name, no duplicate records of the
same paper, and a seal that covers files however they reached the record.
"""
import importlib.util
import json
import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
ATTACHMENT_JSON = ROOT / "murasalat_office/doctype/murasalat_attachment/murasalat_attachment.json"
CORRESPONDENCE_JSON = ROOT / "murasalat_office/doctype/murasalat_correspondence/murasalat_correspondence.json"
REFERRAL_JSON = ROOT / "murasalat_office/doctype/murasalat_referral/murasalat_referral.json"
OVERVIEW_PY = ROOT / "services/overview.py"
RECORDS_PY = ROOT / "services/records.py"
REFERRAL_TEMPLATE = ROOT / "templates/overview/referral.html"


class MurasalatThrow(Exception):
    pass


@pytest.fixture(autouse=True)
def _stubbed_frappe():
    saved = {key: sys.modules.get(key) for key in ("frappe", "frappe.utils")}

    frappe = types.ModuleType("frappe")
    frappe.throw = lambda message, exc=None, **kwargs: (_ for _ in ()).throw(MurasalatThrow(str(message)))
    frappe._ = lambda text: text
    frappe.PermissionError = MurasalatThrow
    frappe.session = types.SimpleNamespace(user="tester@example.com")
    frappe.db = types.SimpleNamespace(get_value=lambda *a, **k: None, exists=lambda *a, **k: True)
    frappe.get_all = lambda *a, **k: []
    frappe.get_doc = lambda *a, **k: None

    utils = types.ModuleType("frappe.utils")
    utils.now_datetime = lambda: "2026-09-24 00:00:00"
    frappe.utils = utils

    sys.modules["frappe"] = frappe
    sys.modules["frappe.utils"] = utils

    yield

    for key, value in saved.items():
        if value is None:
            sys.modules.pop(key, None)
        else:
            sys.modules[key] = value


def _records():
    spec = importlib.util.spec_from_file_location("records_attachments", RECORDS_PY)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _field(path, name):
    return next(field for field in json.loads(path.read_text())["fields"] if field["fieldname"] == name)


# ---------------------------------------------------------------- metadata policy






def test_the_file_hash_is_never_typed_by_a_user():
    assert _field(ATTACHMENT_JSON, "file_hash").get("read_only") == 1


# ---------------------------------------------------------------- duplicates


class _Row:
    def __init__(self, file, attachment_type="Attachment"):
        self.file = file
        self.attachment_type = attachment_type


class _Doc:
    def __init__(self, rows):
        self.attachments = rows








def test_the_snapshot_includes_files_linked_outside_the_table():
    """A file added through the gallery or the uploader is not a row, and was not sealed."""
    source = RECORDS_PY.read_text(encoding="utf-8")

    assert "def _linked_file_snapshot(" in source
    assert '"linked_files": _linked_file_snapshot(doc)' in source
    assert "_linked_file_snapshot(doc)" in source[source.index("def _attachment_snapshot("):]


def test_linked_files_are_read_from_the_record_itself():
    records = _records()
    asked = {}

    def fake_get_all(doctype, **kwargs):
        asked["doctype"] = doctype
        asked.update(kwargs)
        return []

    records.frappe.get_all = fake_get_all

    class Doc:
        name = "MO-00015"
        doctype = "Murasalat Correspondence"

    records._linked_file_snapshot(Doc())

    assert asked["doctype"] == "File"
    assert asked["filters"] == {
        "attached_to_doctype": "Murasalat Correspondence",
        "attached_to_name": "MO-00015",
    }


def test_the_payload_changes_when_a_linked_file_appears():
    """The hash has to move, or the seal would not notice the new file."""
    records = _records()

    class Doc:
        name = "MO-00015"
        doctype = "Murasalat Correspondence"
        correspondence_direction = "Incoming"
        transaction_type = "Letter"
        confidentiality = "Normal"
        importance = "Normal"
        subject = "خطاب"
        external_letter_number = None
        external_letter_date = None
        incoming_source_entity = "ORG-A"
        incoming_target_entry = "ORG-B"
        outgoing_source_entity = None
        outgoing_target_entry = None
        internal_source_entity = None
        internal_target_entry = None
        originating_organization = "ORG-A"
        seal_reason = None
        page_count = 1
        notes = "نص"
        due_date = None
        concerned_person = None
        attachments = []

    records.frappe.get_all = lambda *a, **k: []
    without = records.compute_integrity_hash(Doc())

    records.frappe.get_all = lambda *a, **k: [
        types.SimpleNamespace(name="FILE-1", file_url="/files/extra.pdf", file_name="extra.pdf")
    ]
    with_extra = records.compute_integrity_hash(Doc())

    assert without != with_extra


def test_the_file_lookup_is_ordered_because_one_url_can_have_two_rows():
    source = RECORDS_PY.read_text(encoding="utf-8")

    assert 'filters={"file_url": file_url}' in source
    assert 'order_by="creation desc"' in source


# ---------------------------------------------------------------- the referral can carry attachments


def test_the_referral_has_an_attachment_table_not_just_an_empty_tab():
    fields = json.loads(REFERRAL_JSON.read_text())["fields"]
    names = [field["fieldname"] for field in fields]

    assert "attachments" in names, "the referral's Attachments tab had no table to show"
    table = _field(REFERRAL_JSON, "attachments")
    assert table["fieldtype"] == "Table"
    assert table["options"] == "Murasalat Attachment"

    order = json.loads(REFERRAL_JSON.read_text())["field_order"]
    assert order.index("attachments_tab") < order.index("attachments")




def test_the_referral_panel_shows_its_attachments():
    source = OVERVIEW_PY.read_text(encoding="utf-8")
    template = REFERRAL_TEMPLATE.read_text(encoding="utf-8")

    assert "def _attachment_rows(" in source
    assert 'context["attachments"] = _attachment_rows(doc)' in source
    assert "مرفقات الإحالة" in template
    assert "a.label" in template


def test_a_secret_attachment_never_renders_its_file_name_in_the_panel():
    source = OVERVIEW_PY.read_text(encoding="utf-8")
    body = source[source.index("def _attachment_rows("):]

    assert "مرفق سرّي" in body
    assert "row.file is withheld" not in body
