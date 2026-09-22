"""Contract tests for seal integrity and approval attribution.

Framework-light on purpose: the modules under test are loaded by path with a
minimal ``frappe`` stub, so the rules they encode can be exercised without a
bench. What is pinned here is the *policy*, not Desk rendering:

* a sealed record's body is inside the snapshot, so amending it is detectable;
* there is no silent amendment — reopening requires a reason and preserves the
  previous snapshot in the activity trail;
* the recorded approver cannot be forged and the timestamp cannot be backdated.
"""
import csv
import importlib.util
import json
import sys
import types
from datetime import datetime
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


class MurasalatThrow(Exception):
    """Stands in for the exception ``frappe.throw`` raises."""


class FakeDoc:
    """Minimal stand-in for a Frappe Document."""

    def __init__(self, **kwargs):
        self.doctype = kwargs.pop("doctype", "Murasalat Correspondence")
        self.appended = []
        self.__dict__.update(kwargs)

    def append(self, table, row):
        self.appended.append((table, row))

    def get(self, key, default=None):
        return self.__dict__.get(key, default)

    def is_new(self):
        return False

    def get_doc_before_save(self):
        return self.__dict__.get("_before")

    @property
    def activity_types(self):
        return [row["activity_type"] for _, row in self.appended]


def _install_frappe_stub():
    frappe = types.ModuleType("frappe")

    def throw(message, exc=None, **kwargs):
        raise MurasalatThrow(str(message))

    class PermissionError(Exception):
        pass

    frappe.throw = throw
    frappe._ = lambda text: text
    frappe.PermissionError = PermissionError
    frappe.session = types.SimpleNamespace(user="tester@example.com")
    frappe.db = types.SimpleNamespace(get_value=lambda *a, **k: None)
    frappe.get_doc = lambda *a, **k: None
    frappe.get_all = lambda *a, **k: []

    utils = types.ModuleType("frappe.utils")
    utils.now_datetime = datetime.now
    frappe.utils = utils

    model = types.ModuleType("frappe.model")
    document = types.ModuleType("frappe.model.document")

    class Document:
        pass

    document.Document = Document
    model.document = document

    sys.modules["frappe"] = frappe
    sys.modules["frappe.utils"] = utils
    sys.modules["frappe.model"] = model
    sys.modules["frappe.model.document"] = document


@pytest.fixture(autouse=True)
def _stubbed_frappe():
    """Give every test in this file a deterministic stub, then restore."""
    saved = {
        key: sys.modules.get(key)
        for key in ("frappe", "frappe.utils", "frappe.model", "frappe.model.document")
    }
    _install_frappe_stub()
    yield
    for key, value in saved.items():
        if value is None:
            sys.modules.pop(key, None)
        else:
            sys.modules[key] = value


def _load(name, relative_path):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _records():
    return _load("murasalat_records_under_test", "services/records.py")


def _lifecycle():
    return _load("murasalat_lifecycle_under_test", "services/lifecycle.py")


def _approval_module():
    return _load(
        "murasalat_approval_under_test",
        "murasalat_office/doctype/murasalat_approval_request/murasalat_approval_request.py",
    )


def _sealed_correspondence(**overrides):
    values = dict(
        name="CORR-1",
        correspondence_direction="Incoming",
        transaction_type="Letter",
        confidentiality="Normal",
        importance="Normal",
        subject="خطاب وارد",
        external_letter_number="12/2026",
        external_letter_date="2026-09-01",
        incoming_source_entity="ORG-A",
        incoming_target_entry="ORG-B",
        outgoing_source_entity=None,
        outgoing_target_entry=None,
        internal_source_entity=None,
        internal_target_entry=None,
        originating_organization="ORG-A",
        seal_reason="ملف مكتمل",
        page_count=2,
        notes="نص الخطاب",
        due_date="2026-09-20",
        concerned_person="ORG-C",
        attachments=[],
        record_sealed_on="2026-09-10 09:00:00",
        record_sealed_by="sealer@example.com",
        integrity_hash=None,
        closed_on=None,
        reopened_on=None,
        reopen_reason=None,
    )
    values.update(overrides)
    return FakeDoc(**values)


# ------------------------------------------------------------------ snapshot scope


def test_the_letter_body_is_inside_the_seal_snapshot():
    """The body, its due date and its concerned person are the record's content."""
    records = _records()

    for field in ("notes", "due_date", "concerned_person"):
        assert field in records.IMMUTABLE_AFTER_SEALING, field


def test_editing_the_body_after_sealing_changes_the_integrity_hash():
    records = _records()

    original = _sealed_correspondence()
    amended = _sealed_correspondence(notes="نص مُعدَّل")

    assert records.canonical_payload(original) != records.canonical_payload(amended)
    assert records.compute_integrity_hash(original) != records.compute_integrity_hash(amended)


def test_editing_the_body_after_sealing_is_refused():
    records = _records()

    before = _sealed_correspondence()
    after = _sealed_correspondence(notes="نص مُعدَّل")
    after._before = before

    with pytest.raises(MurasalatThrow) as error:
        records.validate_immutable_fields(after)

    assert "notes" in str(error.value)


def test_a_sealed_record_without_a_snapshot_fails_verification():
    """Claiming to be sealed with no stored snapshot is not a pass."""
    records = _records()

    unverifiable = _sealed_correspondence(integrity_hash=None)
    assert records.verify_integrity(unverifiable, verify_files=False) is False


# ------------------------------------------------------------------ amendment path


def test_reopening_without_a_reason_is_refused():
    lifecycle = _lifecycle()
    doc = _sealed_correspondence()

    with pytest.raises(MurasalatThrow) as error:
        lifecycle.reopen_correspondence(doc)

    assert "reason" in str(error.value).lower()
    assert doc.activity_types == []
    assert doc.record_sealed_on == "2026-09-10 09:00:00"


def test_reopening_lifts_the_seal_and_keeps_the_previous_snapshot():
    lifecycle = _lifecycle()
    doc = _sealed_correspondence(
        integrity_hash="a" * 64,
        closed_on="2026-09-21 10:00:00",
        reopen_reason="تصحيح رقم الخطاب",
    )

    lifecycle.reopen_correspondence(doc)

    assert doc.record_sealed_on is None
    assert doc.record_sealed_by is None
    assert doc.integrity_hash is None
    assert doc.closed_on is None
    assert doc.reopened_by == "tester@example.com"

    assert doc.activity_types == ["Reopened", "Unsealed"]
    unsealed = doc.appended[1][1]
    assert "a" * 64 in unsealed["details"]
    assert "2026-09-10 09:00:00" in unsealed["details"]
    assert "sealer@example.com" in unsealed["details"]
    assert "تصحيح رقم الخطاب" in doc.appended[0][1]["details"]


def test_reopening_an_open_unsealed_record_changes_nothing():
    lifecycle = _lifecycle()
    doc = _sealed_correspondence(record_sealed_on=None, record_sealed_by=None, closed_on=None)

    lifecycle.reopen_correspondence(doc)

    assert doc.activity_types == []
    assert doc.reopened_on is None


def test_the_reason_field_is_declared_and_translated():
    data = json.loads(
        (
            ROOT
            / "murasalat_office/doctype/murasalat_correspondence/murasalat_correspondence.json"
        ).read_text()
    )
    fieldnames = {field["fieldname"] for field in data["fields"]}
    assert "reopen_reason" in fieldnames
    assert "reopen_reason" in data["field_order"]

    sources = _translation_sources()
    assert "Reopen Reason" in sources


def test_the_unsealed_activity_is_a_valid_select_option():
    """Recording the event must not be rejected by the child table's options."""
    data = json.loads(
        (
            ROOT
            / "murasalat_office/doctype/murasalat_correspondence_activity/murasalat_correspondence_activity.json"
        ).read_text()
    )
    for field in data["fields"]:
        if field["fieldname"] == "activity_type" and field.get("fieldtype") == "Select":
            assert "Unsealed" in field.get("options", "").split("\n")
            return
    pytest.fail("activity_type is not a Select; the option list assertion does not apply")


# ------------------------------------------------------------------ approval record


def _approval(before=None, **overrides):
    document = _approval_module().MurasalatApprovalRequest()
    document.is_new = lambda: False
    document.get_doc_before_save = lambda: before
    document.correspondence = "CORR-1"
    document.approval_level = 1
    document.requested_by = "creator@example.com"
    document.requested_on = "2026-09-10 08:00:00"
    document.workflow_state = "Pending"
    document.decision_note = None
    document.approved_by = None
    document.approved_on = None
    for key, value in overrides.items():
        setattr(document, key, value)
    return document


def test_the_decision_is_stamped_with_the_acting_user_and_the_server_time():
    document = _approval(approved_by="tester@example.com")

    document.validate()

    assert document.approved_by == "tester@example.com"
    assert document.approved_on is not None


def test_the_decision_cannot_name_another_user():
    document = _approval(approved_by="someone.else@example.com")

    with pytest.raises(MurasalatThrow):
        document.validate()


def test_a_recorded_decision_cannot_be_rewritten_or_backdated():
    recorded = types.SimpleNamespace(
        approved_by="approver@example.com",
        approved_on="2026-09-12 10:00:00",
        requested_by="creator@example.com",
        correspondence="CORR-1",
    )

    rewritten = _approval(before=recorded, approved_by="approver@example.com", approved_on="2020-01-01 00:00:00")
    with pytest.raises(MurasalatThrow):
        rewritten.validate()

    reassigned = _approval(before=recorded, approved_by="tester@example.com", approved_on="2026-09-12 10:00:00")
    with pytest.raises(MurasalatThrow):
        reassigned.validate()


def test_a_decision_without_an_approver_is_refused():
    document = _approval(approved_on="2026-09-12 10:00:00")

    with pytest.raises(MurasalatThrow):
        document.validate()


def test_a_request_cannot_be_created_already_approved():
    document = _approval(approved_by="tester@example.com")
    document.is_new = lambda: True
    document.requested_on = None

    with pytest.raises(MurasalatThrow):
        document.validate()


# ------------------------------------------------------------------ translation file


def _translation_sources():
    rows = list(csv.reader((ROOT / "translations/ar.csv").read_text(encoding="utf-8").splitlines()))
    return {row[0].strip() for row in rows[1:] if row and row[0].strip()}
