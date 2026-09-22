"""Contracts for the bench-side tooling.

These scripts cannot be imported here — they need frappe — so what is pinned is the shape
of their source, against the two defects they were written to fix.
"""
import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SMOKE = ROOT / "verification/site_smoke.py"
ACCESS = ROOT / "setup/report_access.py"
TASKS = ROOT / "setup/workflow_tasks.py"


def _source(path):
    return path.read_text(encoding="utf-8")


def test_smoke_reports_are_resolved_from_disk_not_by_a_like_filter():
    """A like filter matches the wrong report when one name contains another."""
    source = _source(SMOKE)

    assert '"like"' not in source
    assert "_shipped_reports" in source
    assert "report_name" in source


def test_smoke_uses_the_hook_name_key_that_frappe_actually_reads():
    """The hook entries carry 'name'/'method'; reading 'workflow_action' printed '?'."""
    source = _source(SMOKE)

    assert 'entry.get("name")' in source
    assert "workflow_action" not in source


def test_smoke_checks_verse_support_before_demanding_transition_tasks():
    source = _source(SMOKE)

    assert "_transition_task_field" in source
    assert "transition_tasks" in source


def test_smoke_does_not_require_translation_rows_for_app_csv():
    """App translations load from the CSV, so zero Translation rows is correct."""
    source = _source(SMOKE)

    assert 'frappe.get_all(\n            "Translation"' not in source
    assert "translations/ar.csv" in source
    assert 'frappe.db.exists("Language", "ar")' in source


def test_setup_never_writes_a_report_definition_back_to_the_app_tree():
    """Configuring a site must not edit tracked source files."""
    source = _source(ACCESS)

    assert "report.save(" not in source
    assert 'report.append("roles"' not in source
    assert '"doctype": "Has Role"' in source


def test_setup_commits_because_bench_execute_does_not():
    assert "frappe.db.commit()" in _source(ACCESS)
    assert "frappe.db.commit()" in _source(TASKS)


def test_setup_resolves_report_names_the_same_way_the_smoke_check_does():
    source = _source(ACCESS)

    assert "_shipped_reports" not in source
    assert "report_names()" in source
    assert '"like"' not in source
    assert "report_name" in source


def test_the_task_setup_matches_hooks_by_task_name_not_by_transition_action():
    """A transition's action is what the user clicks; the task names the hook.

    Matching on the action found nothing and reported a working setup as unconfigured.
    """
    source = _source(TASKS)

    assert 'hooks": [task.task for task in tasks' in source
    assert "task.task in hooks" in source
    assert "unattached_hooks" in source


def test_the_task_setup_separates_state_only_transitions_from_problems():
    """Most transitions only move a document along; that is not a defect to report."""
    source = _source(TASKS)

    assert "def problems(" in source
    assert "def state_only_transitions(" in source
    assert "def unattached_hooks(" in source
    assert "def attach(" in source

    problems_body = source[source.index("def problems("):source.index("def state_only_transitions(")]
    assert "no transition task" not in problems_body


def test_attach_supplies_a_group_name_because_the_doctype_prompts_for_one():
    """autoname 'prompt' means the name must be given on insert, not derived."""
    source = _source(TASKS)

    assert "def suggest_group_name(" in source
    assert "def unique_group_name(" in source
    assert '"name": group' in source
    # the convention already used on the site
    assert 'replace(" Workflow", "")' in source


def test_attach_accepts_the_action_label_a_user_can_see():
    """Transition rows are named by a generated hash, which nobody can guess."""
    source = _source(TASKS)

    assert '{"parent": workflow, "action": transition}' in source
    assert "transition = transition_doc.name" in source


def test_the_approval_decision_has_a_writer_not_only_a_guard():
    """Without a writer the read-only fields can never be stamped at all."""
    hooks_source = _source(ROOT / "hooks.py")
    approvals = _source(ROOT / "services/approvals.py")

    assert '"name": "Stamp Approval"' in hooks_source
    assert '"name": "Clear Approval"' in hooks_source
    assert "murasalat_office.services.approvals.stamp_approval" in hooks_source
    assert "murasalat_office.services.approvals.clear_approval" in hooks_source

    assert "def stamp_approval(doc)" in approvals
    assert "def clear_approval(doc)" in approvals
    # the stamp names the acting user and nothing else, and only once
    assert "doc.approved_by = frappe.session.user" in approvals
    assert 'if doc.get("approved_by"):' in approvals

def test_every_hook_declared_in_hooks_py_is_a_real_function():
    hooks_source = _source(ROOT / "hooks.py")

    tree = ast.parse(hooks_source)
    entries = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(
            getattr(target, "id", None) == "workflow_methods" for target in node.targets
        ):
            entries = ast.literal_eval(node.value)

    assert entries, "workflow_methods was not found in hooks.py"

    for entry in entries:
        module_path, _, function_name = entry["method"].rpartition(".")
        module_file = ROOT / (module_path.replace("murasalat_office.", "", 1).replace(".", "/") + ".py")

        if not module_file.is_file():
            module_file = ROOT / "murasalat_office" / (
                module_path.replace("murasalat_office.", "", 1).replace(".", "/") + ".py"
            )

        assert module_file.is_file(), entry["method"]
        module_source = module_file.read_text(encoding="utf-8")
        assert f"def {function_name}(" in module_source, entry["method"]
        assert entry["name"], "a hook entry without a name can never be attached"
