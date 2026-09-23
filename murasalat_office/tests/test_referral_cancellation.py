"""Contract tests for report access, referral cancellation and the shared activity trail."""
import importlib.util
import json
import sys
import types
from datetime import datetime
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
HOLDER = {"parent": None}


class MurasalatThrow(Exception):
    pass


class FakeParent:
    def __init__(self):
        self.appended = []
        self.saved = False
        self.current_holder = "ORG-1"

    def check_permission(self, *args):
        return True

    def append(self, table, row):
        self.appended.append((table, row))

    def get(self, key, default=None):
        return self.__dict__.get(key, default)

    def save(self):
        self.saved = True


class FakeDoc:
    def __init__(self, **kwargs):
        self.doctype = kwargs.pop("doctype", "Murasalat Referral")
        self.appended = []
        self.__dict__.update(kwargs)

    def append(self, table, row):
        self.appended.append((table, row))

    def get(self, key, default=None):
        return self.__dict__.get(key, default)

    def is_new(self):
        return False


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
    frappe.db = types.SimpleNamespace(get_value=lambda *a, **k: None, exists=lambda *a, **k: True)
    frappe.get_doc = lambda *a, **k: HOLDER["parent"]
    frappe.get_all = lambda *a, **k: []

    utils = types.ModuleType("frappe.utils")
    utils.now_datetime = datetime.now
    frappe.utils = utils

    sys.modules["frappe"] = frappe
    sys.modules["frappe.utils"] = utils


@pytest.fixture(autouse=True)
def _stubbed_frappe():
    saved = {key: sys.modules.get(key) for key in ("frappe", "frappe.utils")}
    HOLDER["parent"] = None
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


def _lifecycle():
    return _load("lc_under_test", "services/lifecycle.py")


def _referral(**overrides):
    values = dict(
        name="REF-1",
        referral_number="REF-1",
        correspondence=None,
        sent_on="2026-09-01 08:00:00",
        received_on=None,
        completed_on=None,
        cancelled_on=None,
        cancelled_by=None,
        cancel_reason=None,
    )
    values.update(overrides)
    return FakeDoc(**values)


# ------------------------------------------------------------------ cancellation


def test_cancelling_requires_a_reason():
    lifecycle = _lifecycle()

    with pytest.raises(MurasalatThrow):
        lifecycle.cancel_referral(_referral(cancel_reason="   "))


def test_a_completed_referral_cannot_be_cancelled():
    lifecycle = _lifecycle()

    with pytest.raises(MurasalatThrow) as error:
        lifecycle.cancel_referral(
            _referral(completed_on="2026-09-10 09:00:00", cancel_reason="تأخر الرد")
        )

    assert "completed" in str(error.value).lower()


def test_cancelling_is_attributed_and_recorded_on_the_correspondence():
    lifecycle = _lifecycle()
    HOLDER["parent"] = FakeParent()
    doc = _referral(correspondence="CORR-1", cancel_reason="وصل بالخطأ")

    lifecycle.cancel_referral(doc)

    assert doc.cancelled_on is not None
    assert doc.cancelled_by == "tester@example.com"

    activity = HOLDER["parent"].appended[0][1]
    assert activity["activity_type"] == "Referral Cancelled"
    assert "وصل بالخطأ" in activity["details"]
    assert HOLDER["parent"].saved is True


def test_cancelling_twice_changes_nothing():
    lifecycle = _lifecycle()
    HOLDER["parent"] = FakeParent()
    doc = _referral(correspondence="CORR-1", cancelled_on="2026-09-12 10:00:00", cancel_reason="سابق")

    lifecycle.cancel_referral(doc)

    assert HOLDER["parent"].appended == []


def test_closing_reads_its_filters_as_a_list_not_a_mapping():
    """Closing a correspondence failed with "'list' object is not a mapping".

    OPEN_REFERRAL_FILTERS is a list of triples, so it must spread into a filter list. Any
    attempt to unpack it as a mapping turns every Close into a TypeError.
    """
    lifecycle = _lifecycle()
    captured = {}

    def fake_get_all(doctype, **kwargs):
        captured["doctype"] = doctype
        captured.update(kwargs)
        return []

    lifecycle.frappe.get_all = fake_get_all

    lifecycle._get_open_referrals("MO-00015")

    filters = captured["filters"]
    assert captured["doctype"] == "Murasalat Referral"
    assert isinstance(filters, list), filters
    assert ["correspondence", "=", "MO-00015"] == filters[0]
    # every declared open-referral condition survives into the query
    for condition in lifecycle.OPEN_REFERRAL_FILTERS:
        assert condition in filters, condition


def test_closing_a_correspondence_with_open_referrals_is_refused():
    """The filter has to actually reach the query for the refusal to be meaningful."""
    lifecycle = _lifecycle()
    captured = {}

    def fake_get_all(doctype, **kwargs):
        captured.update(kwargs)
        return [{"name": "MR-00019"}]

    lifecycle.frappe.get_all = fake_get_all
    doc = FakeDoc(
        doctype="Murasalat Correspondence",
        closed_on=None,
        current_holder="ORG-1",
        name="MO-00015",
    )

    with pytest.raises(MurasalatThrow):
        lifecycle.close_correspondence(doc)

    assert isinstance(captured["filters"], list)
    assert doc.closed_on is None


def test_a_cancelled_referral_is_no_longer_open_work():
    """Otherwise a called-off referral would block closing its correspondence forever."""
    lifecycle = _lifecycle()

    assert ["cancelled_on", "is", "not set"] in lifecycle.OPEN_REFERRAL_FILTERS


def test_closing_a_correspondence_twice_changes_nothing():
    lifecycle = _lifecycle()
    doc = FakeDoc(
        doctype="Murasalat Correspondence",
        closed_on="2026-09-20 10:00:00",
        current_holder="ORG-1",
    )

    lifecycle.close_correspondence(doc)

    assert doc.appended == []
    assert doc.closed_on == "2026-09-20 10:00:00"


# ------------------------------------------------------------------ one append path


def test_there_is_exactly_one_activity_append_implementation():
    activity = (ROOT / "services/activity.py").read_text(encoding="utf-8")
    lifecycle = (ROOT / "services/lifecycle.py").read_text(encoding="utf-8")
    controller = (
        ROOT
        / "murasalat_office/doctype/murasalat_correspondence/murasalat_correspondence.py"
    ).read_text(encoding="utf-8")
    import_line = "from murasalat_office.services.activity import append_activity"

    assert activity.count("doc.append(") == 1
    assert "doc.append(" not in lifecycle
    assert "self.append(" not in controller
    assert import_line in lifecycle
    assert import_line in controller


def test_the_cancellation_vocabulary_is_declared_everywhere_it_is_used():
    referral = json.loads(
        (
            ROOT / "murasalat_office/doctype/murasalat_referral/murasalat_referral.json"
        ).read_text(encoding="utf-8")
    )
    fieldnames = {field["fieldname"] for field in referral["fields"]}
    for field in ("cancel_reason", "cancelled_on", "cancelled_by"):
        assert field in fieldnames, field
        assert field in referral["field_order"], field

    activity = json.loads(
        (
            ROOT
            / "murasalat_office/doctype/murasalat_correspondence_activity/murasalat_correspondence_activity.json"
        ).read_text(encoding="utf-8")
    )
    options = next(
        field["options"] for field in activity["fields"] if field["fieldname"] == "activity_type"
    )
    assert "Referral Cancelled" in options.split("\n")

    translations = (ROOT / "translations/ar.csv").read_text(encoding="utf-8")
    for label in ("Cancel Reason", "Cancelled On", "Cancelled By", "Referral Cancelled"):
        assert f"{label}," in translations, label


# ------------------------------------------------------------------ report access


def _report_access():
    return _load("report_access_under_test", "setup/report_access.py")


def test_report_access_covers_every_shipped_report():
    module = _report_access()
    folders = sorted(
        folder.name
        for folder in (ROOT / "murasalat_office/report").iterdir()
        if folder.is_dir() and folder.name != "__pycache__"
    )

    assert module.report_slugs() == folders
    assert len(module.report_slugs()) >= 10


def test_report_access_grants_governance_roles_and_nothing_surprising():
    module = _report_access()

    assert "System Manager" in module.desired_roles()
    for role in module.CORRESPONDENCE_ROLES:
        assert role in module.desired_roles()
    assert "Guest" not in module.desired_roles()
    assert "All" not in module.desired_roles()
