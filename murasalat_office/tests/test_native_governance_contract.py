from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT


def test_no_legacy_policy_modules():
    assert not (APP / "security").exists()
    assert not (APP / "services" / "journey.py").exists()
    assert not (APP / "services" / "delegation.py").exists()
    assert not (APP / "services" / "organization_context.py").exists()
    assert not (APP / "api" / "journey.py").exists()


def test_no_delegation_action_policy_fields():
    data = json.loads((APP / "murasalat_office/doctype/murasalat_delegation/murasalat_delegation.json").read_text())
    fields = {f["fieldname"] for f in data["fields"]}
    assert not fields.intersection({"allow_receive", "allow_start", "allow_complete", "allow_reject", "allow_return"})


def test_reports_use_native_permission_visibility_for_every_exposed_doctype():
    reports = APP / "murasalat_office/report"
    referral_reports = {
        "murasalat_due_today",
        "murasalat_employee_productivity",
        "murasalat_follow_up_queue",
        "murasalat_inbox",
        "murasalat_my_work",
        "murasalat_overdue_referrals",
    }
    for name in referral_reports:
        source = (reports / name / f"{name}.py").read_text()
        assert "permission_condition('c', 'Murasalat Correspondence')" in source or 'permission_condition("c", "Murasalat Correspondence")' in source
        assert "permission_condition('r', 'Murasalat Referral')" in source or 'permission_condition("r", "Murasalat Referral")' in source


def test_operational_summary_does_not_encode_workflow_states():
    source = (APP / "api" / "operations.py").read_text()
    for state in ("Completed", "Rejected", "Returned", "Withdrawn", "Cancelled"):
        assert state not in source


def test_referral_migration_converts_rows_in_place():
    source = (APP / "patches/v0_21_migrate_referrals.py").read_text()
    assert 'doc.insert(' not in source
    assert 'frappe.db.set_value("Murasalat Referral", row.name' in source
    source22 = (APP / "patches/v0_22_preserve_referral_history.py").read_text()
    assert 'frappe.db.set_value("Murasalat Referral", row.name' in source22


def test_referral_tracks_changes():
    data = json.loads((APP / "murasalat_office/doctype/murasalat_referral/murasalat_referral.json").read_text())
    assert data.get("track_changes") == 1


def test_correspondence_syncs_referral_count_once_per_save():
    source = (APP / "murasalat_office/doctype/murasalat_correspondence/murasalat_correspondence.py").read_text()
    assert source.count("self._sync_referral_count()") == 1


def test_reporting_permission_keys_are_alias_specific():
    source = (APP / "reporting.py").read_text()
    assert 'f"visible_{doctype.lower().replace(\' \', \'_\')}_{alias}"' in source


def test_productivity_date_filters_use_completion_date_only():
    source = (APP / "murasalat_office/report/murasalat_employee_productivity/murasalat_employee_productivity.py").read_text()
    assert "COALESCE(r.completed_on, r.modified)" not in source
    assert "DATE(r.completed_on)" in source


def test_sealed_correspondence_initializes_integrity_hash():
    source = (APP / "murasalat_office/doctype/murasalat_correspondence/murasalat_correspondence.py").read_text()
    assert "compute_integrity_hash" in source
    assert "if self.record_sealed_on and not self.integrity_hash" in source
