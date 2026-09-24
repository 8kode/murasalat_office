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


# --- the attachment block the referral slip gained -----------------------------

WITHHELD = "مرفق سرّي — يُطلب من الأرشيف"


def test_the_referral_notification_lists_its_attachments():
    """The slip a recipient signs for must say which papers travel with it.

    The correspondence record printed its attachments; the referral notification did
    not, so somebody signing for a referral had no written list of what came with it.
    """
    source = _source(FORMATS[1])
    assert '{% for att in doc.attachments %}' in source
    assert "المرفقات المرفوعة مع الإحالة" in source


def test_both_formats_withhold_a_secret_attachment_name():
    for entry in FORMATS:
        source = _source(entry)
        assert WITHHELD in source, entry["name"]
        assert "{% if att.is_secret %}" in source, entry["name"]


def test_attachment_types_print_in_arabic_on_both_formats():
    """The stored values are English Select options; an Arabic page maps them."""
    for entry in FORMATS:
        source = _source(entry)
        assert "{% set ATTACHMENT_TYPE_AR" in source, entry["name"]
        assert "ATTACHMENT_TYPE_AR.get(att.attachment_type" in source, entry["name"]


def test_the_attachment_type_map_covers_every_stored_option():
    """A value missing from the map would print as English on an Arabic document."""
    options = {
        line.strip()
        for line in _doctype_fields("Murasalat Attachment")["attachment_type"]["options"].splitlines()
        if line.strip()
    }
    assert options == {"Main Letter", "Attachment", "Reply"}
    for entry in FORMATS:
        source = _source(entry)
        for option in options:
            assert f'"{option}"' in source, (entry["name"], option)


# --- a render pass, not just a parse -------------------------------------------

import datetime as _dt


class _Stub:
    """Yields None for any field a render touches that the test did not set."""

    def __init__(self, **values):
        self.__dict__.update(values)

    def __getattr__(self, name):
        return None


def _frappe_stub():
    utils = _Stub()
    utils.getdate = lambda value=None: value if isinstance(value, _dt.date) else _dt.date(2026, 1, 1)
    utils.get_datetime = lambda value=None: value if isinstance(value, _dt.datetime) else _dt.datetime(2026, 1, 1, 9, 0)
    utils.today = lambda: _dt.date(2026, 1, 1)
    utils.now = lambda: _dt.datetime(2026, 1, 1, 9, 0)
    stub = _Stub()
    stub.utils = utils
    stub.db = _Stub(get_value=lambda *a, **kw: None)
    stub.session = _Stub(user="Administrator")
    stub.has_permission = lambda *a, **kw: True
    return stub


def _render(entry, doc):
    template = jinja2.Environment().from_string(_source(entry))
    return template.render(doc=doc, frappe=_frappe_stub())


def test_both_templates_render_and_no_secret_file_name_reaches_the_page():
    """Parsing is not rendering: this drives the loops and filters for real.

    The record carries one ordinary and one secret attachment, so the assertion that the
    secret file name is absent fails the moment the redaction is removed.
    """
    doc = _Stub(
        name="MC-2026-0001",
        referral_number="REF-2026-0001",
        creation=_dt.datetime(2026, 1, 1, 9, 0),
        attachments=[
            _Stub(attachment_type="Main Letter", file="/files/original-letter.pdf", is_secret=0),
            _Stub(attachment_type="Attachment", file="/files/secret-scan.pdf", is_secret=1),
        ],
    )

    record = _render(FORMATS[0], doc)
    assert "الخطاب الأصلي" in record
    assert "original-letter.pdf" in record
    assert "secret-scan.pdf" not in record

    slip = _render(FORMATS[1], doc)
    assert "المرفقات المرفوعة مع الإحالة (2)" in slip
    assert "منها 1 سرّي" in slip
    assert "الخطاب الأصلي" in slip
    assert "original-letter.pdf" in slip
    assert "secret-scan.pdf" not in slip
    assert WITHHELD in slip
