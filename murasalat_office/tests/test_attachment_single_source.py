"""One source of truth for a record's attachments.

The form used to offer three: the attachments table, an Attachment Gallery field, and
Frappe's sidebar panel. Only the table carries classification and the integrity hash, so the
other two are gone. These tests fail if either comes back.
"""
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DOCTYPE_DIR = ROOT / "murasalat_office/doctype"

DOCTYPE_FILES = {
    "Murasalat Correspondence": DOCTYPE_DIR / "murasalat_correspondence/murasalat_correspondence.json",
    "Murasalat Referral": DOCTYPE_DIR / "murasalat_referral/murasalat_referral.json",
}

FORM_SCRIPTS = {
    "Murasalat Correspondence": DOCTYPE_DIR / "murasalat_correspondence/murasalat_correspondence.js",
    "Murasalat Referral": DOCTYPE_DIR / "murasalat_referral/murasalat_referral.js",
}


def _meta(doctype):
    return json.loads(DOCTYPE_FILES[doctype].read_text(encoding="utf-8"))


@pytest.mark.parametrize("doctype", list(DOCTYPE_FILES))
def test_the_gallery_field_is_gone(doctype):
    """A second list of the same files, with no type, folder or secrecy to record."""
    meta = _meta(doctype)
    fieldnames = [field["fieldname"] for field in meta["fields"]]

    assert "attachments_gallery" not in fieldnames, doctype
    assert "attachments_gallery" not in meta["field_order"], doctype


@pytest.mark.parametrize("doctype", list(DOCTYPE_FILES))
def test_no_leftover_gallery_section_break(doctype):
    meta = _meta(doctype)
    orphaned = [
        field["fieldname"]
        for field in meta["fields"]
        if field["fieldname"].endswith("_gallery_section")
    ]

    assert orphaned == [], f"{doctype}: an empty section break is left behind: {orphaned}"


@pytest.mark.parametrize("doctype", list(DOCTYPE_FILES))
def test_the_attachment_table_is_the_one_source(doctype):
    meta = _meta(doctype)
    table = next(field for field in meta["fields"] if field["fieldname"] == "attachments")

    assert table["fieldtype"] == "Table"
    assert table["options"] == "Murasalat Attachment"

    # a plain Attach/Attach Image field would be a second, unclassified source
    stray = [
        field["fieldname"]
        for field in meta["fields"]
        if field.get("fieldtype") in ("Attach", "Attach Image")
        and field["fieldname"] != "attachments"
    ]
    assert stray == [], f"{doctype}: a second file field remains: {stray}"


@pytest.mark.parametrize("doctype", list(DOCTYPE_FILES))
def test_the_attachments_section_explains_itself(doctype):
    meta = _meta(doctype)
    section = next(field for field in meta["fields"] if field["fieldname"] == "attachments_section")

    assert section.get("description"), f"{doctype}: the section says nothing about what goes in it"


@pytest.mark.parametrize("doctype", list(FORM_SCRIPTS))
def test_the_form_hides_frappes_own_attachments_panel(doctype):
    script = FORM_SCRIPTS[doctype].read_text(encoding="utf-8")

    assert 'find(".form-attachments")' in script, doctype
    assert "toggle(false)" in script, doctype


@pytest.mark.parametrize("doctype", list(FORM_SCRIPTS))
def test_the_form_offers_one_upload_path_into_the_table(doctype):
    script = FORM_SCRIPTS[doctype].read_text(encoding="utf-8")

    assert "new frappe.ui.FileUploader(" in script
    assert 'frm.add_child("attachments"' in script
    assert 'attachment_type: "Attachment"' in script
    assert "frm.refresh_field(\"attachments\")" in script
    # uploaded through the same native widget the sidebar used
    assert 'folder: "Home/Attachments"' in script


@pytest.mark.parametrize("doctype", list(FORM_SCRIPTS))
def test_the_form_does_not_offer_uploads_on_a_sealed_record(doctype):
    script = FORM_SCRIPTS[doctype].read_text(encoding="utf-8")
    body = script[script.index("function murasalat_single_attachment_source"):]

    sealed_guard = body.index("record_sealed_on")
    upload = body.index("new frappe.ui.FileUploader(")

    assert sealed_guard < upload, f"{doctype}: the seal check must run before the upload button"
    assert "المرفقات مقفلة" in body, doctype


@pytest.mark.parametrize("doctype", list(FORM_SCRIPTS))
def test_the_form_script_registers_a_refresh_handler(doctype):
    script = FORM_SCRIPTS[doctype].read_text(encoding="utf-8")

    assert f'frappe.ui.form.on("{doctype}"' in script, doctype
    assert "murasarat_single_attachment_source" not in script, "the helper name is misspelled"
    assert "murasarat_single_attachment_source" not in script.replace("murasarat", "murasalat")
