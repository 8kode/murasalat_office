from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OVERVIEW = (ROOT / "services/overview.py").read_text(encoding="utf-8")
TEMPLATE = (ROOT / "templates/overview/correspondence.html").read_text(encoding="utf-8")
DOC = (ROOT.parent / "docs/PHASE3A_CORRESPONDENCE_EXPERIENCE_ARCHITECTURE.md").read_text(encoding="utf-8")


def test_experience_center_uses_real_doctype_tabs():
    import json

    meta = json.loads((ROOT / "murasalat_office/doctype/murasalat_correspondence/murasalat_correspondence.json").read_text(encoding="utf-8"))
    tabs = [(f["fieldname"], f.get("label")) for f in meta["fields"] if f.get("fieldtype") == "Tab Break"]
    assert tabs == [
        ("data_tab", "البيانات"),
        ("overview_tab", "نظرة عامة"),
        ("referrals_tab", "الإحالات"),
        ("attachments_tab", "المرفقات"),
        ("replies_tab", "الردود الرسمية"),
        ("tracking_tab", "التتبع"),
        ("activity_security_tab", "النشاط والسلامة"),
    ]

    order = meta["field_order"]
    for tab, field in (("overview_tab", "overview_html"), ("referrals_tab", "referrals_html"), ("attachments_tab", "attachments"), ("replies_tab", "replies_html"), ("tracking_tab", "tracking_html"), ("activity_security_tab", "activities")):
        assert order.index(tab) < order.index(field), (tab, field)

    assert "mo-center-nav" not in TEMPLATE


def test_native_attachment_tab_keeps_attachment_table_as_source_of_truth():
    import json

    meta = json.loads((ROOT / "murasalat_office/doctype/murasalat_correspondence/murasalat_correspondence.json").read_text(encoding="utf-8"))
    fields = {f["fieldname"]: f for f in meta["fields"]}
    assert fields["attachments"]["fieldtype"] == "Table"
    assert fields["attachments"]["options"] == "Murasalat Attachment"
    assert "Frappe File" in fields["attachments_note_html"].get("options", "")


def test_attachment_tab_does_not_create_a_new_file_service():
    assert "preview engine" in DOC
    assert "replacement of Frappe File" in DOC


def test_experience_center_does_not_create_a_new_doctype_or_workflow():
    assert "new DocType" in DOC
    assert "No new Workflow" in DOC
    assert "murasalat_overview" not in DOC


def test_transaction_and_referral_workflow_names_are_not_interpreted_by_overview_logic():
    for state in ("Draft", "Sent", "Received", "Completed", "Cancelled", "Registered", "Sealed"):
        assert f'workflow_state") == "{state}"' not in OVERVIEW
        assert f'workflow_state == "{state}"' not in OVERVIEW


def test_domain_evidence_fields_are_explicitly_used():
    for field in ("registered_on", "closed_on", "record_sealed_on", "sent_on", "received_on", "completed_on", "cancelled_on"):
        assert field in OVERVIEW


def test_correspondence_data_tab_preserves_the_transaction_form_fields():
    import json

    meta = json.loads((ROOT / "murasalat_office/doctype/murasalat_correspondence/murasalat_correspondence.json").read_text(encoding="utf-8"))
    order = meta["field_order"]
    expected = [
        "overview_identity_section", "subject", "correspondence_direction", "workflow_state",
        "overview_classification_section", "transaction_type", "importance", "confidentiality",
        "incoming_parties_section", "incoming_source_entity", "overview_party_column_in", "incoming_target_entry",
        "outgoing_parties_section", "outgoing_source_entity", "overview_party_column_out", "outgoing_target_entry",
        "internal_parties_section", "internal_source_entity", "overview_party_column_internal", "internal_target_entry",
        "overview_dates_section", "external_letter_number", "external_letter_date", "due_date",
        "overview_dates_column", "page_count", "concerned_person", "notes",
    ]
    data_index = order.index("data_tab")
    overview_index = order.index("overview_tab")
    assert data_index == 0
    assert all(data_index < order.index(name) < overview_index for name in expected)


def test_overview_contains_latest_movements_without_replacing_native_activity_history():
    import json

    assert "آخر الحركات" in TEMPLATE
    meta = json.loads((ROOT / "murasalat_office/doctype/murasalat_correspondence/murasalat_correspondence.json").read_text(encoding="utf-8"))
    assert meta["field_order"].index("activities") > meta["field_order"].index("activity_security_tab")
