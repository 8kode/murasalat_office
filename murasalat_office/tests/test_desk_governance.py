"""Static contract tests for native Desk governance."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "murasalat_office"


def _json_files():
    return APP.rglob("*.json")


def test_no_business_role_names_in_python():
    for path in APP.rglob("*.py"):
        if path.parent.name == "tests":
            continue
        text = path.read_text()
        for role in ("Murasalat User", "Murasalat Coordinator", "Murasalat Manager", "Murasalat Approver", "Murasalat Auditor", "Murasalat Administrator"):
            assert f'"{role}"' not in text, path


def test_roles_workflows_and_permission_types_are_not_fixtures():
    hooks = (APP / "hooks.py").read_text()
    assert '"Role"' not in hooks
    assert '"Workflow"' not in hooks
    assert '"Workflow State"' not in hooks
    assert '"Permission Type"' not in hooks
    assert "permission_query_conditions" not in hooks
    assert "has_permission" not in hooks


def test_no_custom_permission_type_fixture_exists():
    assert not (APP / "fixtures" / "permission_type.json").exists()


def test_doctypes_do_not_ship_role_permission_rows():
    for path in _json_files():
        data = json.loads(path.read_text())
        if isinstance(data, dict) and data.get("doctype") == "DocType":
            assert "permissions" not in data, path


def test_reports_do_not_ship_role_lists():
    for path in _json_files():
        data = json.loads(path.read_text())
        if isinstance(data, dict) and data.get("doctype") == "Report":
            assert "roles" not in data, path


def test_correspondence_has_native_workflow_field_and_no_fixed_status_select():
    data = json.loads((APP / "murasalat_office/doctype/murasalat_correspondence/murasalat_correspondence.json").read_text())
    fields = {f["fieldname"]: f for f in data["fields"]}
    assert fields["workflow_state"]["fieldtype"] == "Data"
    assert "status" not in fields


def test_referral_is_standalone_and_workflow_governed():
    data = json.loads((APP / "murasalat_office/doctype/murasalat_referral/murasalat_referral.json").read_text())
    fields = {f["fieldname"]: f for f in data["fields"]}
    assert data["istable"] == 0
    assert fields["correspondence"]["fieldtype"] == "Link"
    assert fields["workflow_state"]["fieldtype"] == "Data"
    assert "status" not in fields


def test_workspace_exposes_native_referral_views():
    path = APP / "murasalat_office/workspace/murasalat_office/murasalat_office.json"
    data = json.loads(path.read_text())
    shortcuts = {(item.get("label"), item.get("link_to"), item.get("doc_view")) for item in data.get("shortcuts", [])}
    assert ("Referral Calendar", "Murasalat Referral", "Calendar") in shortcuts
    assert ("Referral Gantt", "Murasalat Referral", "Gantt") in shortcuts


def test_referral_calendar_is_native_calendar_gantt_configuration():
    source = (APP / "murasalat_office/doctype/murasalat_referral/murasalat_referral_calendar.js").read_text()
    assert 'frappe.views.calendar["Murasalat Referral"]' in source
    assert 'start: "due_date"' in source
    assert 'end: "due_date"' in source
    assert 'get_events_method: "frappe.desk.calendar.get_events"' in source
