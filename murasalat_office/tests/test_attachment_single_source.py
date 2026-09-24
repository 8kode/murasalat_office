"""One source of truth for a record's attachments.

The form used to offer three lists of the same files: the attachments table, an Attachment
Gallery field, and Frappe's sidebar panel. The gallery is gone - it recorded nothing but the
file. The panel stays: it is the framework's own upload affordance, and the app now files its
uploads in the table from the framework's File document instead of hiding the panel.
See test_attachment_native_index.py for that half.
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


def _attachment_block(doctype):
    """The attachment code alone - the form has other buttons that are not upload paths."""
    script = FORM_SCRIPTS[doctype].read_text(encoding="utf-8")
    return script[script.index("function murasalat_attachment_rules"):]


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
def test_the_form_no_longer_reaches_into_frappes_own_panel(doctype):
    """Hiding `.form-attachments` selected on markup the framework does not publish.

    The panel uploads natively and the File event files the result in the table, so the form
    script has no reason to touch the sidebar at all.
    """
    script = FORM_SCRIPTS[doctype].read_text(encoding="utf-8")

    assert ".form-attachments" not in script, doctype
    assert "toggle(false)" not in script, doctype
    assert "sidebar" not in _attachment_block(doctype), doctype


@pytest.mark.parametrize("doctype", list(FORM_SCRIPTS))
def test_the_form_offers_no_second_upload_path(doctype):
    """One row per file means one upload affordance: the framework's own panel."""
    block = _attachment_block(doctype)

    assert "FileUploader" not in block, doctype
    assert 'frm.add_child("attachments"' not in block, doctype
    assert "add_custom_button" not in block, doctype


def test_the_correspondence_warns_before_a_sealed_upload():
    """The refusal is server-side; this only saves the user from picking a file first."""
    script = FORM_SCRIPTS["Murasalat Correspondence"].read_text(encoding="utf-8")

    assert "record_sealed_on" in script
    assert "المرفقات مقفلة" in script


def test_the_referral_carries_no_seal_warning():
    """A referral has no seal fields, so there is nothing to warn about."""
    script = FORM_SCRIPTS["Murasalat Referral"].read_text(encoding="utf-8")

    assert "record_sealed_on" not in script
    assert "المرفقات مقفلة" not in script


@pytest.mark.parametrize("doctype", list(FORM_SCRIPTS))
def test_the_form_script_registers_a_refresh_handler(doctype):
    script = FORM_SCRIPTS[doctype].read_text(encoding="utf-8")

    assert f'frappe.ui.form.on("{doctype}"' in script, doctype
    assert "murasarat_single_attachment_source" not in script, "the helper name is misspelled"
    assert "murasarat_single_attachment_source" not in script.replace("murasarat", "murasalat")
