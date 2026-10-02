import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_official_letter_fields_exist_on_the_outgoing_correspondence():
    data = json.loads((ROOT / "murasalat_office/doctype/murasalat_correspondence/murasalat_correspondence.json").read_text())
    fields = {f["fieldname"]: f for f in data["fields"]}
    for name in ("salutation", "closing_phrase", "signatory_name", "signatory_position", "approval_entity", "preparation_entity", "prepared_on"):
        assert name in fields
    assert fields["approval_entity"]["options"] == "Department"
    assert fields["preparation_entity"]["options"] == "Department"


def test_reply_studio_uses_native_dialog_and_server_api():
    source = (ROOT / "murasalat_office/doctype/murasalat_correspondence/murasalat_correspondence.js").read_text()
    assert "new frappe.ui.Dialog" in source
    assert "Reply by Letter" in source
    assert "murasalat_office.api.operations.create_reply_draft" in source


def test_reply_print_format_is_shipped():
    meta = json.loads((ROOT / "murasalat_office/print_format/murasalat_official_reply/murasalat_official_reply.json").read_text())
    assert meta["doc_type"] == "Murasalat Correspondence"
    assert meta["name"] == "Murasalat Official Reply"
    html = (ROOT / "murasalat_office/print_format/murasalat_official_reply/murasalat_official_reply.html").read_text()
    for token in ("السادة", "الموضوع", "signatory_name", "signatory_position", "closing_phrase"):
        assert token in html


def test_workflow_independence_is_explicit_in_provision_and_notifications():
    provision = (ROOT / "setup/provision.py").read_text()
    notifications = (ROOT / "setup/notifications.py").read_text()
    assert "workflow_state" not in provision
    assert "workflow_state" not in notifications
    assert "doc.sent_on and not doc.completed_on and not doc.cancelled_on" in notifications
    assert "received_on" in notifications and "completed_on" in notifications
