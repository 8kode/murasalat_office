from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]


def _source(path):
    return (ROOT / path).read_text(encoding="utf-8")


def test_provision_does_not_ship_fixed_workflows():
    source = _source("setup/provision.py")
    assert "WORKFLOWS = [" not in source
    assert "_ensure_workflow" not in source
    assert "_top_up_transition_tasks" not in source


def test_governance_plan_declares_site_defined_workflows():
    source = _source("setup/governance_plan.py")
    assert '"site_defined": True' in source
    assert "Draft" not in source
    assert "Registered" not in source
    assert "Completed" not in source


def test_provision_is_parseable():
    ast.parse(_source("setup/provision.py"))
