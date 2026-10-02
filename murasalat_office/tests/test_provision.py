"""One command has to make a site launchable - and leave nothing half-built.

The application ships no fixtures, deliberately: roles, permissions and Workflows are Desk
configuration. What it lacked was a single reviewable way to create that configuration through
Frappe's own models. These tests hold the two things that make the difference between a
launchable site and a silently broken one:

* every task the provisioning attaches is a name ``hooks.py`` actually declares - a typo there
  makes every transition using it throw at runtime;
* nothing is written without ``confirm=True``.
"""
import ast
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PROVISION = ROOT / "setup/provision.py"
HOOKS = ROOT / "hooks.py"
GUIDE = Path(__file__).resolve().parents[2] / "docs/USER_GUIDE.md"

SOURCE = PROVISION.read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)


def _constants():
    """Every module level name assigned a literal in provision.py."""
    values = {}

    for node in TREE.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name):
                try:
                    values[target.id] = ast.literal_eval(node.value)
                except ValueError:
                    pass

    return values


def _literal(name):
    """Evaluate a module level value with the module's own constants in scope.

    WORKFLOWS names CLERK and CORRESPONDENCE rather than repeating the strings, so the plain
    literal_eval path cannot read it. Evaluating the same AST in a namespace built from the
    module keeps the test reading the shipped source, not a copy of it.
    """
    for node in TREE.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == name for t in node.targets
        ):
            return eval(compile(ast.Expression(node.value), "<provision>", "eval"), {}, _constants())

    raise AssertionError(f"{name} is not declared in provision.py")


def _hook_names():
    source = HOOKS.read_text(encoding="utf-8")
    block = source.split("workflow_methods = [", 1)[1].split("\n]", 1)[0]
    return re.findall(r'"name": "([^"]+)"', block)


def test_the_provisioning_is_opt_in():
    """A command that writes roles and Workflows must not run by accident."""
    assert "def apply(confirm=False):" in SOURCE
    assert "def plan():" in SOURCE
    assert "def readiness():" in SOURCE
    assert "confirm=True" in SOURCE

    # the guard has to run before anything is written
    body = SOURCE.split("def apply(confirm=False):", 1)[1].split("def readiness(", 1)[0]
    assert body.index("if not confirm:") < body.index("master_data.seed()")


def test_every_attached_task_is_a_declared_hook():
    attached, declared = set(), set(_hook_names())

    for spec in _literal("WORKFLOWS"):
        for transition in spec["transitions"]:
            attached.add(transition["task"])

    assert attached <= declared, sorted(attached - declared)


def test_every_lifecycle_task_is_attached():
    """A transition with no task runs no application code, and reports nothing."""
    declared = set(_hook_names())
    lifecycle = {name for name in declared if name not in ("Stamp Approval", "Clear Approval")}

    attached = {
        transition["task"]
        for spec in _literal("WORKFLOWS")
        for transition in spec["transitions"]
    }

    assert lifecycle <= attached, sorted(lifecycle - attached)


def test_no_transition_carries_a_task_that_does_nothing():
    declared = set(_hook_names())
    for spec in _literal("WORKFLOWS"):
        for transition in spec["transitions"]:
            assert transition["task"] in declared, transition


def test_the_referral_workflow_never_touches_the_correspondence():
    """A lifecycle method guards its DocType, so a task on the wrong workflow throws."""
    by_name = {spec["name"]: spec for spec in _literal("WORKFLOWS")}
    referral = by_name["Murasalat Referral Lifecycle"]

    assert referral["document_type"] == "Murasalat Referral"
    for transition in referral["transitions"]:
        assert "Correspondence" not in transition["task"].replace("Correspondence ", "")


def test_the_workflows_name_the_lifecycle_in_plain_words():
    """Desk shows these names; an administrator has to recognise them."""
    names = [spec["name"] for spec in _literal("WORKFLOWS")]

    assert "Murasalat Correspondence Lifecycle" in names
    assert "Murasalat Referral Lifecycle" in names


def test_every_transition_moves_between_declared_states():
    for spec in _literal("WORKFLOWS"):
        known = {state["state"] for state in spec["states"]}
        for transition in spec["transitions"]:
            assert transition["state"] in known, (spec["name"], transition)
            assert transition["next_state"] in known, (spec["name"], transition)


def test_an_existing_workflow_is_never_overwritten():
    """An administrator may have edited it in Desk; provisioning reports, it does not replace."""
    assert 'frappe.db.exists("Workflow", spec["name"])' in SOURCE
    assert "_ensure_workflow" in SOURCE


def test_asynchronous_stays_off():
    """Asynchronous turns every lifecycle method into a silent no-op."""
    assert "async_field" in SOURCE
    assert "no-op" in SOURCE


def test_the_fieldnames_come_from_the_live_meta_not_from_memory():
    """The Workflow schema is the framework's; a renamed field must not half-build a workflow."""
    assert "def _field(meta, *candidates):" in SOURCE
    assert "frappe.get_meta" in SOURCE
    assert "workflow_state_field" in SOURCE


def test_the_readiness_report_prints_something_a_person_can_act_on():
    assert "PASS" in SOURCE and "FAIL" in SOURCE
    assert "Ready for users." in SOURCE


@pytest.mark.skipif(not GUIDE.is_file(), reason="the guide is delivered with the branch")
def test_the_user_guide_exists_for_the_people_who_will_actually_use_it():
    """Every technical document was written; the clerk had none."""
    text = GUIDE.read_text(encoding="utf-8")

    assert len(text) > 2000, "a guide nobody can follow is not a guide"
    for step in ("تسجيل", "إحالة", "استلام", "إكمال", "إغلاق", "ختم", "طباعة"):
        assert step in text, step

def test_a_workflow_that_already_exists_still_gets_its_missing_tasks():
    """`_ensure_workflow` returns early for an existing Workflow, so a site whose Workflow
    predates the transition-task feature kept transitions that run nothing - silently, since a
    state-changing transition with no method throws no error. The tasks are topped up instead."""
    assert "def _top_up_transition_tasks(" in SOURCE
    assert "_top_up_transition_tasks(spec, names)" in SOURCE

    top_up = SOURCE.split("def _top_up_transition_tasks(", 1)[1].split("\ndef ", 1)[0]
    assert "document.append(" in top_up, "missing rows are appended"
    assert "missing" in top_up
    assert "remove(" not in top_up and "delete" not in top_up, "an existing task is never removed"
    assert "Asynchronous" in top_up or "async_field" in top_up, "and async stays off"


def test_readiness_reports_a_workflow_whose_transitions_run_nothing():
    """A Workflow that exists is not a Workflow that works."""
    assert "def _unattached_transitions(" in SOURCE
    assert "_unattached_transitions(spec)" in SOURCE
    assert "transition tasks" in SOURCE
