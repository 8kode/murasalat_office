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
        if name == "murasalat_employee_productivity":
            assert "ignore_permissions=False" in source
            assert "frappe.get_list" in source
        else:
            assert "ignore_permissions=False" in source
            assert "frappe.qb.get_query" in source


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


def test_correspondence_does_not_count_referrals_during_validation():
    source = (APP / "murasalat_office/doctype/murasalat_correspondence/murasalat_correspondence.py").read_text()
    assert "_sync_referral_count" not in source
    assert 'frappe.db.count("Murasalat Referral"' not in source


def test_productivity_date_filters_use_completion_date_only():
    source = (APP / "murasalat_office/report/murasalat_employee_productivity/murasalat_employee_productivity.py").read_text()
    assert "COALESCE(r.completed_on, r.modified)" not in source
    assert "completed_on" in source


def test_sealed_correspondence_initializes_integrity_hash():
    source = (APP / "murasalat_office/doctype/murasalat_correspondence/murasalat_correspondence.py").read_text()
    assert "compute_integrity_hash" in source
    assert "if self.record_sealed_on and not self.integrity_hash" in source


def test_native_contextual_dashboards_exist_for_core_transaction_doctypes():
    for name in (
        "murasalat_correspondence/murasalat_correspondence_dashboard.py",
        "murasalat_referral/murasalat_referral_dashboard.py",
        "murasalat_approval_request/murasalat_approval_request_dashboard.py",
    ):
        assert (APP / "murasalat_office/doctype" / name).exists()


def test_correspondence_dashboard_links_referrals_and_approvals_by_native_fields():
    source = (APP / "murasalat_office/doctype/murasalat_correspondence/murasalat_correspondence_dashboard.py").read_text()
    assert '"Murasalat Referral": "correspondence"' in source
    assert '"Murasalat Approval Request": "correspondence"' in source


def test_reverse_dashboards_use_native_internal_links():
    referral = (APP / "murasalat_office/doctype/murasalat_referral/murasalat_referral_dashboard.py").read_text()
    approval = (APP / "murasalat_office/doctype/murasalat_approval_request/murasalat_approval_request_dashboard.py").read_text()
    assert '"Murasalat Correspondence": "correspondence"' in referral
    assert '"Murasalat Correspondence": "correspondence"' in approval


def test_core_doctypes_use_human_readable_link_titles():
    correspondence = json.loads((APP / "murasalat_office/doctype/murasalat_correspondence/murasalat_correspondence.json").read_text())
    referral = json.loads((APP / "murasalat_office/doctype/murasalat_referral/murasalat_referral.json").read_text())
    assert correspondence.get("title_field") == "subject"
    assert correspondence.get("show_title_field_in_link") == 1
    assert referral.get("title_field") == "referral_number"
    assert referral.get("show_title_field_in_link") == 1


def test_workspace_exposes_native_operational_entry_points():
    workspace = json.loads((APP / "murasalat_office/workspace/murasalat_office/murasalat_office.json").read_text())
    shortcuts = {item.get("label"): item for item in workspace.get("shortcuts", [])}
    assert shortcuts["New Referral"]["link_to"] == "Murasalat Referral"
    assert shortcuts["New Referral"]["type"] == "DocType"
    links = workspace.get("links", [])
    overdue = next(item for item in links if item.get("label") == "Overdue Referrals")
    assert overdue["link_to"] == "Murasalat Overdue Referrals"
    assert overdue["report_ref_doctype"] == "Murasalat Referral"


def test_operational_ux_does_not_ship_notification_or_workflow_fixtures():
    assert not (APP / "fixtures").exists()
    assert (ROOT.parent / "docs/EXPERT_AUDIT_v0.27.3.md").exists()


def test_workspace_uses_native_quick_lists_and_number_cards():
    workspace = json.loads((APP / "murasalat_office/workspace/murasalat_office/murasalat_office.json").read_text())
    quick_lists = {item["label"]: item for item in workspace.get("quick_lists", [])}
    assert "Recent Correspondence" in quick_lists
    assert "Recent Referrals" in quick_lists
    assert "Follow-up Referrals" in quick_lists
    cards = list((APP / "murasalat_office/number_card").glob("*/*.json"))
    assert len(cards) >= 4




def test_correspondence_does_not_expose_permission_sensitive_referral_count():
    data = json.loads((APP / "murasalat_office/doctype/murasalat_correspondence/murasalat_correspondence.json").read_text())
    fields = {field["fieldname"] for field in data["fields"]}
    assert "referral_count" not in fields

def test_correspondence_naming_is_independent_from_select_labels():
    data = json.loads((APP / "murasalat_office/doctype/murasalat_correspondence/murasalat_correspondence.json").read_text())
    assert data.get("autoname") == "format:MO-.#####"


def test_referral_has_native_human_readable_numbering():
    data = json.loads((APP / "murasalat_office/doctype/murasalat_referral/murasalat_referral.json").read_text())
    assert data.get("autoname") == "format:MR-.#####"
    source = (APP / "murasalat_office/doctype/murasalat_referral/murasalat_referral.py").read_text()
    assert "self.referral_number = self.name" in source


def test_governance_covers_delegation_and_membership():
    source = (APP / "services/governance.py").read_text()
    assert '"Murasalat Delegation"' in source
    assert '"Murasalat User Organization Membership"' in source


def test_reports_prefer_native_query_builder_for_simple_operational_queries():
    for name in ("murasalat_due_today", "murasalat_follow_up_queue", "murasalat_my_work", "murasalat_overdue_referrals", "murasalat_work_queue", "murasalat_inbox"):
        source = (APP / "murasalat_office/report" / name / f"{name}.py").read_text()
        assert "frappe.qb.get_query" in source
        assert "ignore_permissions=False" in source
    for name in ("murasalat_due_today", "murasalat_follow_up_queue", "murasalat_my_work", "murasalat_overdue_referrals"):
        source = (APP / "murasalat_office/report" / name / f"{name}.py").read_text()
        assert "enrich_with_correspondence" in source


def test_legacy_migrations_use_cross_database_database_abstractions():
    for name in ("schema_repair.py", "v0_21_migrate_referrals.py", "v0_22_preserve_referral_history.py"):
        source = (APP / "patches" / name).read_text()
        assert "SHOW COLUMNS" not in source
        assert "SHOW TABLES" not in source
    for name in ("v0_21_migrate_referrals.py", "v0_22_preserve_referral_history.py"):
        source = (APP / "patches" / name).read_text()
        assert "frappe.db.multisql" in source


def test_no_dead_comment_only_membership_client_script():
    assert not (APP / "murasalat_office/doctype/murasalat_user_organization_membership/murasalat_user_organization_membership.js").exists()


def test_erpnext_is_not_declared_as_an_unused_runtime_dependency():
    hooks = (APP / "hooks.py").read_text()
    assert "required_apps" not in hooks
    assert "erpnext" not in hooks


def test_delegation_uses_current_expression_naming_syntax():
    data = json.loads((APP / "murasalat_office/doctype/murasalat_delegation/murasalat_delegation.json").read_text())
    assert data.get("autoname") == "format:MD-.#####"


def test_save_time_integrity_check_does_not_read_attachment_content():
    source = (APP / "murasalat_office/doctype/murasalat_correspondence/murasalat_correspondence.py").read_text()
    assert "verify_integrity(self, verify_files=False)" in source


def test_explicit_integrity_api_keeps_full_file_verification():
    source = (APP / "api/operations.py").read_text()
    assert "verify_integrity(doc)" in source


def test_delegated_scope_batches_organization_resolution():
    source = (APP / "murasalat_office/report/murasalat_inbox/murasalat_inbox.py").read_text()
    assert '"originating_organization": ["in", restricted_orgs]' in source
    assert '["recipient_organization", "in", restricted_orgs]' in source
    assert '"correspondence", "in", scoped_names' in source
