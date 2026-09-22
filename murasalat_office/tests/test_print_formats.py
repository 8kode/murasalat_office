"""Contract tests for the two shipped print formats.

Print formats break in production rather than in review: a mistyped field name renders
an empty cell and a Jinja slip raises only when somebody tries to print. Both are caught
here instead — the templates are parsed by Jinja itself and every ``doc.<field>`` they
reference is checked against the DocType metadata.
"""
import json
import re
from pathlib import Path

import jinja2

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT
PRINT_FORMAT_DIR = APP / "murasalat_office/print_format"

FORMATS = [
    {
        "name": "Murasalat Correspondence Print",
        "folder": "murasalat_correspondence_print",
        "doc_type": "Murasalat Correspondence",
    },
    {
        "name": "Murasalat Referral Notification",
        "folder": "murasalat_referral_notification",
        "doc_type": "Murasalat Referral",
    },
]

# Fields every document carries at runtime without being declared in its JSON.
STANDARD_FIELDS = {
    "name",
    "creation",
    "modified",
    "modified_by",
    "owner",
    "docstatus",
    "doctype",
    "idx",
    "parent",
    "parentfield",
    "parenttype",
}

# Frappe exposes this module to print-format Jinja; anything else is not available.
ALLOWED_FRAPPE_ATTRIBUTES = {
    "session",
    "db",
    "utils",
    "has_permission",
    "get_doc",
    "get_all",
    "get_list",
    "get_value",
    "formatdate",
    "nowdate",
    "utils.now",
    "utils.today",
    "utils.getdate",
    "utils.get_datetime",
    "utils.now_datetime",
    "utils.formatdate",
    "session.user",
}


def _doctype_fields(doctype):
    """Return declared fieldnames plus the child-table linkage of a DocType."""
    slug = doctype.lower().replace(" ", "_")
    path = APP / "murasalat_office/doctype" / slug / f"{slug}.json"
    data = json.loads(path.read_text())
    return {field["fieldname"]: field for field in data["fields"]}


def _source(entry):
    return (PRINT_FORMAT_DIR / entry["folder"] / f"{entry['folder']}.html").read_text()


def test_both_formats_are_packed_where_frappe_expects_them():
    """get_doc_path puts a Print Format at <module>/print_format/<scrubbed>/<scrubbed>."""
    for entry in FORMATS:
        folder = PRINT_FORMAT_DIR / entry["folder"]
        assert folder.is_dir(), entry["folder"]
        assert (folder / f"{entry['folder']}.json").is_file(), entry["name"]
        assert (folder / f"{entry['folder']}.html").is_file(), entry["name"]


def test_format_metadata_declares_a_standard_jinja_format():
    for entry in FORMATS:
        data = json.loads((PRINT_FORMAT_DIR / entry["folder"] / f"{entry['folder']}.json").read_text())
        assert data["doctype"] == "Print Format"
        assert data["name"] == entry["name"]
        assert data["module"] == "Murasalat Office"
        assert data["doc_type"] == entry["doc_type"]
        assert data["standard"] == "Yes"
        assert data["print_format_type"] == "Jinja"
        assert data["disabled"] == 0


def test_embedded_html_matches_the_shipped_template():
    """The JSON carries the template too, so a site works even if only the row is read."""
    for entry in FORMATS:
        folder = PRINT_FORMAT_DIR / entry["folder"]
        data = json.loads((folder / f"{entry['folder']}.json").read_text())
        assert data["html"] == (folder / f"{entry['folder']}.html").read_text()


def test_templates_are_valid_jinja():
    """A syntax error here is a runtime failure the first time somebody prints."""
    environment = jinja2.Environment()
    for entry in FORMATS:
        environment.parse(_source(entry), filename=entry["folder"])


def test_templates_are_arabic_and_right_to_left():
    for entry in FORMATS:
        source = _source(entry)
        assert 'dir="rtl"' in source, entry["name"]
        assert "direction: rtl" in source, entry["name"]
        # an Arabic-first document must not fall back to Latin-only font defaults
        assert "Noto Naskh Arabic" in source, entry["name"]


def test_printed_labels_do_not_depend_on_translation_files():
    """Print output stays Arabic even on a site with an incomplete ar.csv."""
    for entry in FORMATS:
        source = _source(entry)
        assert '{{ _(' not in source, entry["name"]
        assert '{% trans' not in source, entry["name"]


def test_every_document_field_used_in_a_template_exists():
    for entry in FORMATS:
        source = _source(entry)
        fields = _doctype_fields(entry["doc_type"])
        used = set(re.findall(r"\bdoc\.([a-zA-Z_][a-zA-Z0-9_]*)", source))

        assert used, entry["name"]
        unknown = used - set(fields) - STANDARD_FIELDS
        assert not unknown, (entry["name"], sorted(unknown))


def test_every_child_table_loop_uses_real_child_fields():
    """Resolve each `for x in doc.<table>` loop against the table's own DocType."""
    for entry in FORMATS:
        source = _source(entry)
        fields = _doctype_fields(entry["doc_type"])

        for loop_var, table in re.findall(
            r"\{%-?\s*for\s+(\w+)\s+in\s+doc\.(\w+)\s*%\}", source
        ):
            field = fields[table]
            assert field["fieldtype"] == "Table", (entry["name"], table)
            child = _doctype_fields(field["options"])

            used = set(re.findall(rf"\b{loop_var}\.([a-zA-Z_][a-zA-Z0-9_]*)", source))
            unknown = used - set(child) - STANDARD_FIELDS
            assert not unknown, (entry["name"], table, sorted(unknown))


def test_templates_only_reach_for_frappe_attributes_that_exist():
    for entry in FORMATS:
        source = _source(entry)
        branches = set(re.findall(r"\bfrappe\.((?:\w+\.)*\w+)", source))
        for branch in branches:
            root = branch.split(".")[0]
            assert root in {
                "session", "db", "utils", "has_permission", "get_doc", "get_all",
                "get_list", "get_value", "formatdate", "nowdate",
            }, (entry["name"], branch)


def test_the_referral_notification_guards_the_parent_correspondence():
    """A notification must not leak a file the printing user cannot open."""
    source = _source(FORMATS[1])
    assert "frappe.has_permission(" in source
    assert "مقيّد" in source
    assert "can_read_parent" in source


def test_shipping_print_formats_introduces_no_governance():
    hooks = (APP / "hooks.py").read_text()
    assert "fixtures = [" not in hooks
    assert not (APP / "fixtures").exists()
    for entry in FORMATS:
        data = json.loads((PRINT_FORMAT_DIR / entry["folder"] / f"{entry['folder']}.json").read_text())
        assert "permissions" not in data
