from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "murasalat_office"


def test_approval_request_doctype_is_removed():
    assert not (APP / "doctype/murasalat_approval_request").exists()


def test_approval_service_is_removed():
    assert not (ROOT / "services/approvals.py").exists()


def test_approval_workflow_hooks_are_removed():
    source = (ROOT / "hooks.py").read_text()
    assert "Stamp Approval" not in source
    assert "Clear Approval" not in source
    assert "services.approvals" not in source


def test_membership_doctype_is_removed():
    assert not (APP / "doctype/murasalat_user_organization_membership").exists()


def test_membership_unique_index_hook_is_removed():
    source = (ROOT / "hooks.py").read_text()
    repair = (ROOT / "patches/schema_repair.py").read_text()
    assert "ensure_membership_unique_index" not in source
    assert "ensure_membership_unique_index" not in repair


def test_inbox_has_no_custom_organization_membership_scope():
    source = (APP / "report/murasalat_inbox/murasalat_inbox.py").read_text()
    metadata = (APP / "report/murasalat_inbox/murasalat_inbox.json").read_text()
    script = (APP / "report/murasalat_inbox/murasalat_inbox.js").read_text()
    for value in (source, metadata, script):
        assert "My Organization" not in value
        assert "Murasalat User Organization Membership" not in value


def test_correspondence_has_no_retired_user_holder_projection():
    source = (APP / "doctype/murasalat_correspondence/murasalat_correspondence.json").read_text()
    assert "current_holder_user" not in source


def test_governance_no_longer_lists_removed_doctypes():
    governance = (ROOT / "services/governance.py").read_text()
    plan = (ROOT / "setup/governance_plan.py").read_text()
    for value in (governance, plan):
        assert "Murasalat Approval Request" not in value
        assert "Murasalat User Organization Membership" not in value
