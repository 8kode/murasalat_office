"""Contract: every declared workflow_methods entry is a real, documented task.

The application ships no Workflow configuration (Native-First). What it does own is
the promise that the hook names in ``hooks.py`` resolve to guarded lifecycle
methods and are documented for whoever configures the Desk Workflow.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT
DOC = ROOT.parent / "docs/WORKFLOW_GOVERNANCE.md"

EXPECTED_TASKS = [
    ('Register Correspondence', 'register_correspondence', 'Murasalat Correspondence'),
    ('Close Correspondence', 'close_correspondence', 'Murasalat Correspondence'),
    ('Seal Correspondence', 'seal_correspondence', 'Murasalat Correspondence'),
    ('Reopen Correspondence', 'reopen_correspondence', 'Murasalat Correspondence'),
    ('Send Referral', 'send_referral', 'Murasalat Referral'),
    ('Receive Referral', 'receive_referral', 'Murasalat Referral'),
    ('Complete Referral', 'complete_referral', 'Murasalat Referral'),
    ('Stamp Approval', 'stamp_approval', 'Murasalat Approval Request'),
    ('Clear Approval', 'clear_approval', 'Murasalat Approval Request'),
    ('Cancel Referral', 'cancel_referral', 'Murasalat Referral'),
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


def _method_source(method):
    """The source file that defines the method a hook entry names."""
    module, _, _ = method.rpartition(".")
    relative = module.replace("murasalat_office.", "", 1).replace(".", "/") + ".py"
    return (APP / relative).read_text()


def test_hook_declares_exactly_the_registered_tasks():
    entries = _hook_entries()
    assert [name for name, _ in entries] == [name for name, _, _ in EXPECTED_TASKS]


def test_hook_names_are_unique():
    names = [name for name, _ in _hook_entries()]
    assert len(names) == len(set(names))


def test_every_hook_method_resolves_to_a_real_guarded_function():
    """A hook is worthless if it cannot be imported, so the method must exist."""
    for name, method in _hook_entries():
        source = _method_source(method)
        _, _, func = method.rpartition(".")
        assert f"def {func}(doc)" in source, name


def test_every_hook_guards_its_target_doctype():
    """Each method refuses to run on anything but its own doctype.

    The guard may compare against the literal doctype or against a module constant, so the
    doctype is looked for in the method's module rather than inline in its body.
    """
    entries = {name: method for name, method in _hook_entries()}

    for name, func, doctype in EXPECTED_TASKS:
        source = _method_source(entries[name])
        body = _function_body(source, func)

        assert "doc.doctype !=" in body, name
        assert doctype in source, f"{name}: nothing in its module mentions {doctype}"


def test_documentation_covers_every_task_and_the_async_trap():
    source = DOC.read_text(encoding="utf-8")

    for name, _, _ in EXPECTED_TASKS:
        assert name in source, name

    assert "Asynchronous" in source
    assert "Workflow Transition Task" in source
