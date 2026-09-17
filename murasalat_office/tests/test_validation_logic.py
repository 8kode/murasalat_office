"""Framework-light tests for data-validation rules.

These tests intentionally stub only the tiny Frappe surface used by the validators,
so they can run in CI without requiring a full Bench runtime.
"""
import importlib
import sys
import types
from datetime import date, datetime
from pathlib import Path


class ValidationError(Exception):
    pass


class PermissionError(Exception):
    pass


def _load(module_name):
    """Import a module against isolated Frappe stubs without leaking sys.modules state."""
    frappe = types.ModuleType("frappe")
    frappe.throw = lambda message, exc=None: (_ for _ in ()).throw((exc or ValidationError)(message))
    frappe.PermissionError = PermissionError
    frappe._ = lambda value: value
    frappe.session = types.SimpleNamespace(user="tester@example.com")
    frappe.db = types.SimpleNamespace(exists=lambda *args, **kwargs: None)

    document = type("Document", (), {})
    frappe_model = types.ModuleType("frappe.model")
    frappe_document = types.ModuleType("frappe.model.document")
    frappe_document.Document = document

    utils = types.ModuleType("frappe.utils")
    utils.now_datetime = lambda: datetime(2026, 9, 9, 12, 0, 0)
    utils.today = lambda: "2026-09-09"
    utils.getdate = lambda value: value if isinstance(value, date) else date.fromisoformat(str(value))

    replacements = {
        "frappe": frappe,
        "frappe.model": frappe_model,
        "frappe.model.document": frappe_document,
        "frappe.utils": utils,
    }
    target_names = {module_name, "frappe", "frappe.model", "frappe.model.document", "frappe.utils"}
    previous = {name: sys.modules.get(name) for name in target_names}
    previous_murasalat = {name: value for name, value in sys.modules.items() if name.startswith("murasalat_office.")}
    try:
        sys.modules.update(replacements)
        sys.modules.pop(module_name, None)
        return importlib.import_module(module_name)
    finally:
        for name in list(sys.modules):
            if name.startswith("murasalat_office.") and name not in previous_murasalat:
                sys.modules.pop(name, None)
        for name, value in previous_murasalat.items():
            sys.modules[name] = value
        for name in target_names:
            old = previous[name]
            if old is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = old


def _obj(**values):
    return types.SimpleNamespace(**values)


def test_referral_recipient_validation():
    mod = _load("murasalat_office.murasalat_office.doctype.murasalat_referral.murasalat_referral")
    good = object.__new__(mod.MurasalatReferral)
    good.recipient_type = "User"
    good.recipient_user = "user@example.com"
    good.recipient_organization = None
    mod.MurasalatReferral.validate(good)

    bad = object.__new__(mod.MurasalatReferral)
    bad.recipient_type = "User"
    bad.recipient_user = None
    bad.recipient_organization = None
    try:
        mod.MurasalatReferral.validate(bad)
    except ValidationError:
        pass
    else:
        raise AssertionError("Invalid User referral was accepted")


def test_delegation_validation():
    mod = _load("murasalat_office.murasalat_office.doctype.murasalat_delegation.murasalat_delegation")
    good = object.__new__(mod.MurasalatDelegation)
    good.delegator = "a@example.com"
    good.delegate = "b@example.com"
    good.from_date = "2026-09-09"
    good.to_date = "2026-09-10"
    mod.MurasalatDelegation.validate(good)

    bad = object.__new__(mod.MurasalatDelegation)
    bad.delegator = "a@example.com"
    bad.delegate = "a@example.com"
    bad.from_date = "2026-09-09"
    bad.to_date = "2026-09-10"
    try:
        mod.MurasalatDelegation.validate(bad)
    except ValidationError:
        pass
    else:
        raise AssertionError("Self-delegation was accepted")


def test_approval_request_initialization_and_immutability():
    mod = _load("murasalat_office.murasalat_office.doctype.murasalat_approval_request.murasalat_approval_request")
    new_doc = object.__new__(mod.MurasalatApprovalRequest)
    new_doc.requested_by = None
    new_doc.requested_on = None
    new_doc.correspondence = "CORR-001"
    new_doc.approval_level = 1
    new_doc.is_new = lambda: True
    new_doc.get_doc_before_save = lambda: None
    mod.MurasalatApprovalRequest.validate(new_doc)
    assert new_doc.requested_by == "tester@example.com"
    assert new_doc.requested_on is not None

    changed = object.__new__(mod.MurasalatApprovalRequest)
    changed.requested_by = "other@example.com"
    changed.requested_on = datetime(2026, 9, 9, 12, 0, 0)
    changed.correspondence = "CORR-001"
    changed.approval_level = 1
    changed.is_new = lambda: False
    changed.get_doc_before_save = lambda: _obj(requested_by="tester@example.com", correspondence="CORR-001")
    try:
        mod.MurasalatApprovalRequest.validate(changed)
    except PermissionError:
        pass
    else:
        raise AssertionError("requested_by immutability was bypassed")


def test_membership_date_validation_and_duplicate_contract():
    mod = _load("murasalat_office.murasalat_office.doctype.murasalat_user_organization_membership.murasalat_user_organization_membership")
    good = object.__new__(mod.MurasalatUserOrganizationMembership)
    good.valid_from = "2026-09-09"
    good.valid_to = "2026-09-10"
    good.user = "user@example.com"
    good.organization = "ORG-001"
    good.name = "MEM-001"
    good.doctype = "Murasalat User Organization Membership"
    mod.MurasalatUserOrganizationMembership.validate(good)

    bad = object.__new__(mod.MurasalatUserOrganizationMembership)
    bad.valid_from = "2026-09-11"
    bad.valid_to = "2026-09-10"
    bad.user = "user@example.com"
    bad.organization = "ORG-001"
    bad.name = "MEM-002"
    bad.frappe = None
    try:
        mod.MurasalatUserOrganizationMembership.validate(bad)
    except ValidationError:
        pass
    else:
        raise AssertionError("Invalid membership date range was accepted")


def test_membership_future_start_is_valid_data_but_excluded_by_inbox_scope():
    mod = _load("murasalat_office.murasalat_office.doctype.murasalat_user_organization_membership.murasalat_user_organization_membership")
    doc = object.__new__(mod.MurasalatUserOrganizationMembership)
    doc.valid_from = "2026-09-11"
    doc.valid_to = "2026-09-20"
    doc.user = "user@example.com"
    doc.organization = "ORG-001"
    doc.name = "MEM-003"
    doc.doctype = "Murasalat User Organization Membership"
    mod.MurasalatUserOrganizationMembership.validate(doc)


def test_attachment_hash_is_not_recomputed_when_file_is_unchanged():
    mod = _load("murasalat_office.murasalat_office.doctype.murasalat_attachment.murasalat_attachment")
    doc = object.__new__(mod.MurasalatAttachment)
    doc.file = "/private/files/test.pdf"
    doc.file_hash = "existing-hash"
    doc.get_doc_before_save = lambda: _obj(file=doc.file)
    doc._hash_file_url = lambda value: (_ for _ in ()).throw(AssertionError("hash should not be recomputed"))
    mod.MurasalatAttachment.validate(doc)


def test_delegated_inbox_scope_groups_delegations_by_organization():
    mod = _load("murasalat_office.murasalat_office.report.murasalat_inbox.murasalat_inbox")
    grouped = mod._group_delegations([
        {"delegator": "a@example.com", "organization": "ORG-A"},
        {"delegator": "a@example.com", "organization": "ORG-B"},
        {"delegator": "b@example.com", "organization": None},
    ])
    assert grouped["a@example.com"] == {"ORG-A", "ORG-B"}
    assert grouped["b@example.com"] == {""}


def test_delegated_inbox_scope_batches_restricted_organizations():
    mod = _load("murasalat_office.murasalat_office.report.murasalat_inbox.murasalat_inbox")
    calls = []

    def fake_get_list(doctype, **kwargs):
        calls.append((doctype, kwargs))
        if doctype == "Murasalat Correspondence":
            return [
                {"name": "CORR-A", "originating_organization": "ORG-A"},
                {"name": "CORR-B", "originating_organization": "ORG-B"},
            ]
        return []

    class Row:
        def __init__(self, name):
            self.referral_id = name

    def fake_query(filters):
        calls.append(("referral", filters))
        return [Row("REF-1")]

    mod.frappe.get_list = fake_get_list
    mod._query_referrals = fake_query
    rows = mod._query_delegated_referrals(
        [
            {"delegator": "a@example.com", "organization": "ORG-A"},
            {"delegator": "a@example.com", "organization": "ORG-B"},
        ],
        [],
    )

    assert [row.referral_id for row in rows] == ["REF-1"]
    correspondence_calls = [c for c in calls if c[0] == "Murasalat Correspondence"]
    referral_calls = [c for c in calls if c[0] == "referral"]
    assert len(correspondence_calls) == 1
    assert len(referral_calls) == 2
    assert correspondence_calls[0][1]["filters"]["originating_organization"] == ["in", ["ORG-A", "ORG-B"]]
    assert any(["recipient_organization", "in", ["ORG-A", "ORG-B"]] in call[1] for call in referral_calls)
    assert any(["correspondence", "in", ["CORR-A", "CORR-B"]] in call[1] for call in referral_calls)


def test_activity_catalog_matches_events_emitted_by_controller():
    import json

    root = Path(__file__).resolve().parents[1]
    doctype = json.loads((root / "murasalat_office/doctype/murasalat_correspondence_activity/murasalat_correspondence_activity.json").read_text())
    options = next(field["options"] for field in doctype["fields"] if field["fieldname"] == "activity_type").splitlines()
    assert options == ["Created", "Status Changed", "Sealed", "Reopened"]


def test_correspondence_lifecycle_activity_detection():
    mod = _load("murasalat_office.murasalat_office.doctype.murasalat_correspondence.murasalat_correspondence")
    doc = object.__new__(mod.MurasalatCorrespondence)
    doc.is_new = lambda: False
    old = _obj(workflow_state="Draft", record_sealed_on=None, reopened_on=None)
    doc.workflow_state = "Review"
    doc.record_sealed_on = "2026-09-09 12:00:00"
    doc.reopened_on = None
    doc.get_doc_before_save = lambda: old
    events = []
    doc._append_activity = lambda activity_type, **kwargs: events.append(activity_type)
    mod.MurasalatCorrespondence.before_save(doc)
    assert events == ["Status Changed", "Sealed"]


def test_api_contract_exposes_governance_and_normalizes_dates():
    root = Path(__file__).resolve().parents[1]
    source = (root / "api/operations.py").read_text()
    assert "def get_governance_health" in source
    assert 'frappe.only_for("System Manager")' in source
    assert "frappe.utils.getdate(r.due_date)" in source


def test_records_use_sealing_terminology_and_shared_file_hash():
    root = Path(__file__).resolve().parents[1]
    source = (root / "services/records.py").read_text()
    attachment = (root / "murasalat_office/doctype/murasalat_attachment/murasalat_attachment.py").read_text()
    assert "IMMUTABLE_AFTER_SEALING" in source
    assert "IMMUTABLE_AFTER_REGISTRATION" not in source
    assert "from murasalat_office.services.records import hash_file_url" in attachment


def test_membership_dead_clearance_fields_are_removed_and_unique_index_is_declared():
    root = Path(__file__).resolve().parents[1]
    source = (root / "murasalat_office/doctype/murasalat_user_organization_membership/murasalat_user_organization_membership.json").read_text()
    repair = (root / "patches/schema_repair.py").read_text()
    assert "access_level" not in source
    assert "max_clearance_rank" not in source
    assert "murasalat_user_org_unique_idx" in repair



def test_integrity_verification_fails_closed_when_attachment_hash_is_missing():
    mod = _load("murasalat_office.services.records")
    doc = _obj(integrity_hash="snapshot", attachments=[_obj(file="/files/a.pdf", file_hash=None)])
    assert mod.verify_integrity(doc) is False


def test_membership_audit_trail_is_enabled():
    import json
    root = Path(__file__).resolve().parents[1]
    source = json.loads((root / "murasalat_office/doctype/murasalat_user_organization_membership/murasalat_user_organization_membership.json").read_text())
    assert source["track_changes"] == 1

def test_permission_aware_reporting_uses_restricted_subject_placeholder():
    root = Path(__file__).resolve().parents[1]
    source = (root / "services/reporting.py").read_text()
    assert '[Restricted]' in source
    assert 'ignore_permissions=False' in source
