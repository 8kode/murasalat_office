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


def test_the_task_setup_keeps_tasks_synchronous_and_idempotent():
    source = _source(TASKS)

    assert '"asynchronous": 0' in source
    assert "if row[\"attached\"]" in source
    assert "supports_transition_tasks()" in source


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
