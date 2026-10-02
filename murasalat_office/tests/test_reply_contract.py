"""Static/domain contract tests for the official reply flow.

These tests intentionally do not require a live Frappe site. The integration path is exercised
by the app's normal controller/ORM at runtime; these tests protect the architectural contract
from accidental regressions in source metadata and service wiring.
"""
from pathlib import Path
import ast
import json

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT


def _read(relative):
    return (APP / relative).read_text()


def _json(relative):
    return json.loads((APP / relative).read_text())


def test_reply_uses_existing_links_table_and_no_duplicate_reply_field():
    data = _json("murasalat_office/doctype/murasalat_correspondence/murasalat_correspondence.json")
    fields = {field["fieldname"]: field for field in data["fields"]}
    assert fields["links"]["fieldtype"] == "Table"
    assert fields["links"]["options"] == "Murasalat Correspondence Link"
    assert "reply_to_correspondence" not in fields


def test_reply_relationship_vocabularly_contains_reply_to():
    data = _json("murasalat_office/doctype/murasalat_correspondence_link/murasalat_correspondence_link.json")
    fields = {field["fieldname"]: field for field in data["fields"]}
    assert "Reply To" in fields["relationship_type"]["options"].splitlines()


def test_reply_domain_rules_are_server_side():
    source = _read("murasalat_office/doctype/murasalat_correspondence/murasalat_correspondence.py")
    assert "def _validate_reply_relationships" in source
    assert "target.correspondence_direction != \"Incoming\"" in source
    assert "self.outgoing_target_entry != target.incoming_source_entity" in source
    assert 'relationship_type == "Reply To"' in source


def test_completion_result_is_a_real_server_required_field():
    data = _json("murasalat_office/doctype/murasalat_referral/murasalat_referral.json")
    fields = {field["fieldname"]: field for field in data["fields"]}
    assert fields["completion_result"]["fieldtype"] == "Small Text"

    source = _read("murasalat_office/doctype/murasalat_referral/murasalat_referral.py")
    lifecycle = _read("services/lifecycle.py")
    assert "def _validate_completion_result" in source
    assert "A Completion Result is required" in source
    assert "A Completion Result is required" in lifecycle


def test_integrity_snapshot_covers_links():
    source = _read("services/records.py")
    assert '"links",\n}' in source
    assert '"links": [' in source
    assert '"relationship_type": row.relationship_type' in source


def test_reply_service_uses_permission_aware_referral_reads_for_user_visible_data():
    source = _read("services/reply.py")
    assert "frappe.get_list(" in source
    assert "completion_result" in source
    assert 'frappe.has_permission(doc, ptype="create_reply")' in source
    assert 'reply.signatory_name' in source
    assert 'reply.signatory_position' in source
    assert 'reply.closing_phrase' in source
    assert 'frappe.has_permission(CORRESPONDENCE, ptype="create")' in source
    assert "ignore_permissions=True" not in source
    assert '"open_referrals": open_referrals' not in source
    assert '"open_referral_count": len(open_referrals)' in source


def test_reply_api_is_thin_and_whitelisted():
    source = _read("api/operations.py")
    assert '@frappe.whitelist()\ndef get_reply_context' in source
    assert '@frappe.whitelist()\ndef create_reply_draft' in source
    assert "services.reply" in source


def test_ui_never_treats_client_permission_as_security_boundary():
    source = _read("murasalat_office/doctype/murasalat_correspondence/murasalat_correspondence.js")
    assert "get_reply_context" in source
    assert "create_reply_draft" in source
    assert "frappe.perm.has_perm" not in source


def test_create_reply_permission_is_part_of_explicit_governance_plan():
    source = _read("setup/governance_plan.py")
    assert '"create_reply": 1' in source
    provision = _read("setup/provision.py")
    assert 'CREATE_REPLY_PERMISSION = "create_reply"' in provision
    assert '"Permission Type"' in provision
    assert "ensure_custom_permission_type" in provision


def test_no_reply_workflow_method_was_added():
    source = _read("hooks.py")
    assert '"Create Reply"' not in source


def test_reply_service_parses_as_python():
    ast.parse(_read("services/reply.py"))
