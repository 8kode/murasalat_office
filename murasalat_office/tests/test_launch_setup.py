"""Contract tests for the launch setup helpers.

The module is framework-light on purpose: the site bootstrap runs on a real Bench,
so what is pinned here is the shape of the seed data and the idempotency contract,
plus the guarantee that no governance is created behind the administrator's back.
"""
import importlib
import json
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT
MODULE = "murasalat_office.setup.master_data"


def _load(created, existing):
    """Import the seed module against a captured in-memory Frappe surface."""
    frappe = types.ModuleType("frappe")

    class FakeDoc:
        def __init__(self, values):
            self.values = dict(values)

        def insert(self, ignore_permissions=False):
            created.append(self.values)
            existing.add((self.values["doctype"], self.values["__name__"]))

    def get_doc(values):
        # The production code inserts from a dict; record the resulting name so the
        # second call sees it as existing, which is what makes the seed idempotent.
        record = dict(values)
        doctype = record["doctype"]
        name = None
        for candidate in record.values():
            if isinstance(candidate, str) and candidate not in (doctype,):
                name = candidate
                break
        record["__name__"] = name
        return FakeDoc(record)

    frappe.db = types.SimpleNamespace(
        exists=lambda doctype, name: (doctype, name) in existing
    )
    frappe.get_doc = get_doc
    frappe._ = lambda value: value

    previous = sys.modules.get("frappe")
    previous_module = sys.modules.get(MODULE)
    sys.modules["frappe"] = frappe
    sys.modules.pop(MODULE, None)
    try:
        module = importlib.import_module(MODULE)
    finally:
        if previous is None:
            sys.modules.pop("frappe", None)
        else:
            sys.modules["frappe"] = previous
        if previous_module is None:
            sys.modules.pop(MODULE, None)
        else:
            sys.modules[MODULE] = previous_module
    return module


def _fresh():
    created = []
    existing = set()

    def exists(doctype, name):
        return (doctype, name) in existing

    return created, existing, exists


def test_seed_creates_every_record_then_reports_them_as_existing():
    created, existing, _exists = _fresh()
    module = _load(created, existing)

    total = sum(len(records) for _, _, records in module.MASTER_DATA)

    first = module.seed()
    assert len(first["created"]) == total
    assert first["exists"] == []
    assert len(created) == total

    # The second run must create nothing: the seed is safe to re-run.
    created.clear()
    second = module.seed()
    assert second["created"] == []
    assert len(second["exists"]) == total
    assert created == []


def test_dry_run_creates_nothing_and_reports_the_plan():
    created, existing, _ = _fresh()
    module = _load(created, existing)

    report = module.seed(dry_run=True)

    assert report["dry_run"] is True
    assert created == []
    assert report["created"] == []
    assert len(report["planned"]) == sum(
        len(records) for _, _, records in module.MASTER_DATA
    )


def test_correspondence_field_defaults_resolve_to_seeded_records():
    """The four defaults on Murasalat Correspondence must exist after a seed."""
    correspondence = json.loads(
        (
            APP
            / "murasalat_office/doctype/murasalat_correspondence/murasalat_correspondence.json"
        ).read_text()
    )
    fields = {f["fieldname"]: f for f in correspondence["fields"]}

    expected = {
        "transaction_type": "مذكرة",
        "confidentiality": "عام",
        "importance": "متوسط",
        "correspondence_direction": "Internal",
    }

    created, existing, _ = _fresh()
    module = _load(created, existing)
    seeded = {
        (doctype, record[field])
        for doctype, field, records in module.MASTER_DATA
        for record in records
    }

    for fieldname, default in expected.items():
        field = fields[fieldname]
        assert field["default"] == default, fieldname
        assert (field["options"], default) in seeded, (fieldname, default)


def test_registration_directions_are_seeded_by_their_exact_names():
    """register_correspondence switches on these three strings."""
    lifecycle = (APP / "services/lifecycle.py").read_text()
    source = (APP / "setup/master_data.py").read_text()
    for direction in ("Incoming", "Outgoing", "Internal"):
        assert f'"{direction}":' in lifecycle, direction
        assert f'"correspondence_direction": "{direction}"' in source, direction


def test_verify_reports_every_launch_critical_value():
    created, existing, _ = _fresh()
    module = _load(created, existing)

    missing = module.verify()
    assert len(missing) == len(module.REQUIRED_BY_DEFAULTS)

    report = module.seed()
    assert report["missing_required"] == []


def test_setup_creates_no_governance():
    """No role, permission row, workflow or fixture may be created by the bootstrap."""
    source = (APP / "setup/master_data.py").read_text()
    for forbidden in ('"Role"', '"DocPerm"', '"Workflow"', '"Workflow State"', '"Permission Type"'):
        assert forbidden not in source, forbidden

    plan = (APP / "setup/governance_plan.py").read_text()
    assert "fixtures = [" not in plan
    hooks = (APP / "hooks.py").read_text()
    assert "fixtures = [" not in hooks
    assert not (APP / "fixtures").exists()


def test_governance_plan_is_preview_only_by_default():
    plan = (APP / "setup/governance_plan.py").read_text()
    # The plan must be readable without touching the database, and any materialising
    # path must require an explicit opt-in from the caller.
    assert "def describe(" in plan
    assert "apply=False" in plan
    assert "def plan(" in plan
