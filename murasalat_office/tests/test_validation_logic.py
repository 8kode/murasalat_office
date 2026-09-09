"""Framework-light tests for data-validation rules.

These tests intentionally stub only the tiny Frappe surface used by the validators,
so they can run in CI without requiring a full Bench runtime.
"""
import importlib
import sys
import types
from datetime import date, datetime


class ValidationError(Exception):
    pass


class PermissionError(Exception):
    pass


def _load(module_name):
    frappe = types.ModuleType("frappe")
    frappe.throw = lambda message, exc=None: (_ for _ in ()).throw((exc or ValidationError)(message))
    frappe.PermissionError = PermissionError
    frappe._ = lambda value: value
    frappe.session = types.SimpleNamespace(user="tester@example.com")

    document = type("Document", (), {})
    frappe_model = types.ModuleType("frappe.model")
    frappe_document = types.ModuleType("frappe.model.document")
    frappe_document.Document = document

    utils = types.ModuleType("frappe.utils")
    utils.now_datetime = lambda: datetime(2026, 9, 9, 12, 0, 0)
    utils.getdate = lambda value: value if isinstance(value, date) else date.fromisoformat(value)

    sys.modules.update({
        "frappe": frappe,
        "frappe.model": frappe_model,
        "frappe.model.document": frappe_document,
        "frappe.utils": utils,
    })
    return importlib.import_module(module_name)


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
