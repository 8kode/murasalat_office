"""Contract: every declared workflow_methods entry is a real, documented task.

The application ships no Workflow configuration (Native-First). What it does own is
the promise that the seven hook names in ``hooks.py`` resolve to guarded lifecycle
methods and are documented for whoever configures the Desk Workflow.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT
DOC = ROOT.parent / "docs/WORKFLOW_GOVERNANCE.md"

EXPECTED_TASKS = [
    ("Register Correspondence", "register_correspondence", "Murasalat Correspondence"),
    ("Close Correspondence", "close_correspondence", "Murasalat Correspondence"),
    ("Seal Correspondence", "seal_correspondence", "Murasalat Correspondence"),
    ("Reopen Correspondence", "reopen_correspondence", "Murasalat Correspondence"),
    ("Send Referral", "send_referral", "Murasalat Referral"),
    ("Receive Referral", "receive_referral", "Murasalat Referral"),
    ("Complete Referral", "complete_referral", "Murasalat Referral"),
]


def _hooks_source():
    return (APP / "hooks.py").read_text()


def _hook_entries():
    source = _hooks_source()
    block = source.split("workflow_methods = [", 1)[1].split("\n]", 1)[0]
    return re.findall(r'"name":\s*"([^"]+)"\s*,\s*"method":\s*"([^"]+)"', block)


def _lifecycle_source():
    return (APP / "services/lifecycle.py").read_text()


def _function_body(source, func):
    return source.split(f"def {func}(doc)", 1)[1].split("\ndef ", 1)[0]


def test_hook_declares_exactly_the_seven_lifecycle_tasks():
    entries = _hook_entries()
    assert [name for name, _ in entries] == [name for name, _, _ in EXPECTED_TASKS]


def test_every_hook_method_resolves_to_a_lifecycle_function():
    for name, method in _hook_entries():
        module, _, func = method.rpartition(".")
        assert module == "murasalat_office.services.lifecycle", name
        assert f"def {func}(doc)" in _lifecycle_source(), name


def test_every_lifecycle_method_guards_its_target_doctype():
    source = _lifecycle_source()
    for name, func, doctype in EXPECTED_TASKS:
        body = _function_body(source, func)
        assert "doc.doctype !=" in body, name
        assert f'"{doctype}"' in body, name


def test_task_names_are_not_duplicated_and_stay_stable():
    names = [name for name, _, _ in EXPECTED_TASKS]
    assert len(names) == len(set(names)) == 7
    hooks = _hooks_source()
    for name in names:
        assert f'"name": "{name}"' in hooks, name


def test_desktop_configuration_is_not_shipped_as_fixtures():
    hooks = _hooks_source()
    assert "fixtures = [" not in hooks
    assert not (APP / "fixtures").exists()
    assert not (APP / "security").exists()


def test_governance_diagnoses_task_misconfiguration_read_only():
    source = (APP / "services/governance.py").read_text()
    assert "def workflow_task_readiness" in source
    assert "workflow_methods" in source
    assert "Workflow Transition Tasks" in source
    assert "asynchronous" in source
    # the diagnostic must stay read-only
    assert ".insert(" not in source
    assert ".save(" not in source
    assert "frappe.db.set_value" not in source


def test_documentation_covers_every_task_and_the_async_trap():
    doc = DOC.read_text()
    assert "Workflow Transition Tasks" in doc
    for name, _, _ in EXPECTED_TASKS:
        assert f"`{name}`" in doc, name
    assert "Asynchronous" in doc
    assert "enqueue_after_commit" in doc
