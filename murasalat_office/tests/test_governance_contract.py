from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]


def test_governance_report_exists():
    report = ROOT / "murasalat_office/report/murasalat_security_health/murasalat_security_health.json"
    data = json.loads(report.read_text())
    assert data["report_type"] == "Script Report"
    assert data["name"] == "Murasalat Security Health"


def test_governance_service_is_read_only():
    source = (ROOT / "services/governance.py").read_text()
    assert ".insert(" not in source
    assert ".save(" not in source
    assert "frappe.db.set_value" not in source


def test_package_version_matches_release():
    pyproject = (ROOT.parent / "pyproject.toml").read_text()
    app_init = (ROOT / "__init__.py").read_text()
    assert 'version = "0.22.1"' in pyproject
    assert '__version__ = "0.22.1"' in app_init


def test_eslint_configuration_is_valid_json():
    import json as _json
    _json.loads((ROOT.parent / ".eslintrc").read_text())


def test_setup_version_matches_release():
    setup = (ROOT.parent / "setup.py").read_text()
    assert "version='0.22.1'" in setup


def test_sealed_attachment_changes_are_rejected():
    source = (ROOT / "services/records.py").read_text()
    assert "def validate_sealed_attachments" in source
    assert "Attachments cannot be added, removed, or changed after the correspondence is sealed." in source
