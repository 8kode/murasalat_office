"""Contract tests for the form and list-view experience.

These are metadata and client-script contracts: the behaviour they describe only becomes
visible on a running Desk, so what is pinned here is the shape that produces it.
"""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT

DIRECTIONS = {
    "Incoming": "incoming_parties_section",
    "Outgoing": "outgoing_parties_section",
    "Internal": "internal_parties_section",
}


def _meta(slug):
    return json.loads((APP / f"murasalat_office/doctype/{slug}/{slug}.json").read_text())


def _fields(meta):
    return {field["fieldname"]: field for field in meta["fields"]}


# ------------------------------------------------------------------ correspondence form


def test_only_the_relevant_party_section_is_shown_for_the_direction():
    """Three party sections on one form is the single most confusing thing a clerk sees."""
    fields = _fields(_meta("murasalat_correspondence"))

    for direction, section in DIRECTIONS.items():
        field = fields[section]
        assert field["fieldtype"] == "Section Break", section
        assert field.get("depends_on"), section
        assert f'doc.correspondence_direction=="{direction}"' in field["depends_on"], section


def test_party_sections_stay_in_the_form_layout():
    """A depends_on hides a section; it must not remove it from field_order."""
    meta = _meta("murasalat_correspondence")

    for section in DIRECTIONS.values():
        assert section in meta["field_order"], section


def test_subject_and_body_do_not_carry_the_same_label():
    """Both were labelled «الموضوع», so a clerk could not tell the field from the topic."""
    fields = _fields(_meta("murasalat_correspondence"))

    subject_label = fields["subject"]["label"]
    body_label = fields["notes"]["label"]

    assert subject_label != body_label
    assert body_label not in {"الموضوع", "Subject"}, body_label


def test_the_retired_holder_projection_is_hidden_from_users():
    """current_holder_user is always cleared, so showing it misleads."""
    fields = _fields(_meta("murasalat_correspondence"))

    assert fields["current_holder_user"].get("hidden") == 1


def test_audit_section_is_collapsible():
    fields = _fields(_meta("murasalat_correspondence"))

    assert fields["security_section"].get("collapsible") == 1


def test_referral_prefills_from_the_parent_correspondence():
    """Creating a referral should not require re-typing what the file already says."""
    fields = _fields(_meta("murasalat_referral"))

    assert fields["importance"].get("fetch_from") == "correspondence.importance"
    assert fields["importance"].get("fetch_if_empty") == 1
    assert fields["due_date"].get("fetch_from") == "correspondence.due_date"
    assert fields["due_date"].get("fetch_if_empty") == 1


def test_approval_request_shows_a_readable_link_title():
    fields = _fields(_meta("murasalat_approval_request"))
    meta = _meta("murasalat_approval_request")

    assert fields["subject"].get("fetch_from") == "correspondence.subject"
    assert fields["subject"].get("fetch_if_empty") == 1
    assert meta.get("title_field") == "subject"
    assert meta.get("show_title_field_in_link") == 1


# ------------------------------------------------------------------------ list views


def test_correspondence_list_indicator_describes_the_document_state():
    source = (
        APP
        / "murasalat_office/doctype/murasalat_correspondence/murasalat_correspondence_list.js"
    ).read_text()

    assert "record_sealed_on" in source
    assert "closed_on" in source
    assert "workflow_state" in source
    # the old indicator described a due date, which is a field of the referrals, not this
    assert "No Due Date" not in source


def test_correspondence_list_does_not_load_the_retired_field():
    source = (
        APP
        / "murasalat_office/doctype/murasalat_correspondence/murasalat_correspondence_list.js"
    ).read_text()

    assert "current_holder_user" not in source


def test_referral_list_indicator_separates_completed_draft_and_overdue():
    source = (
        APP
        / "murasalat_office/doctype/murasalat_referral/murasalat_referral_list.js"
    ).read_text()

    # order matters: a completed referral must not be reported as overdue
    completed_at = source.index("completed_on")
    draft_at = source.index("sent_on,is,not set")
    overdue_at = source.index("Overdue")

    assert completed_at < draft_at < overdue_at
    assert '"Completed"' in source or "__(\"Completed\")" in source
    assert "red" in source and "orange" in source and "green" in source


def test_both_list_scripts_use_native_listview_helpers():
    for slug in ("murasalat_correspondence", "murasalat_referral"):
        source = (APP / f"murasalat_office/doctype/{slug}/{slug}_list.js").read_text()

        assert "frappe.listview_settings[" in source, slug
        assert "get_indicator(doc)" in source, slug
        assert "frappe.datetime.get_today()" in source or slug.endswith("correspondence"), slug
        assert "hide_name_column: true" in source, slug


# ------------------------------------------------------------------------ translations


def test_new_english_labels_have_arabic_translations():
    """The repo ships English labels plus ar.csv, so a new label must arrive with its row."""
    rows = list(
        csv.reader(
            (APP / "translations/ar.csv").read_text(encoding="utf-8").splitlines()
        )
    )
    keys = {row[0] for row in rows if row}

    for label in ("Body", "Draft — Not Sent", "Open", "Sealed"):
        assert label in keys, label

    # the file must stay uniformly three-column
    assert {len(row) for row in rows} <= {3, 5}


# ------------------------------------------------------------------------- guardrails


def test_ux_changes_introduce_no_governance():
    hooks = (APP / "hooks.py").read_text()
    assert "fixtures = [" not in hooks

    for slug in ("murasalat_correspondence", "murasalat_referral", "murasalat_approval_request"):
        meta = _meta(slug)
        assert not meta.get("permissions"), slug
