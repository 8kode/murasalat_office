"""The attachment vocabulary is master data, not code.

What a file *is* (its type) and where its paper original is filed are two tables a site owns and
extends from Desk. This replaces a Select field, whose options could only change with a code
change, and a free-text folder field, which collided with Frappe's own notion of a folder and
produced values like "dfs".

The app keeps only what the framework cannot express: the type, the physical location, and the
integrity seal. Everything else about an attachment - storage, linking, permissions, duplicate
detection, folders, sharing - is Frappe's File document doing its job.
"""
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
REPO = Path(__file__).resolve().parents[2]
DT = ROOT / "murasalat_office/doctype"
MASTER_DATA = ROOT / "setup/master_data.py"
RECORDS = ROOT / "services/records.py"
PATCHES = ROOT / "patches.txt"

MASTERS = {
    "Murasalat Attachment Type": DT / "murasalat_attachment_type/murasalat_attachment_type.json",
    "Murasalat Archive Location": DT / "murasalat_archive_location/murasalat_archive_location.json",
}

# Everything the app ships except its tests and its migrations. A migration has to name the
# column it renamed, and a test has to name the thing it guards, so neither can join a search
# for a name that must not come back.
APP_SOURCES = sorted(
    p for p in ROOT.rglob("*")
    if p.is_file() and p.suffix in (".py", ".js", ".html", ".json")
    and "__pycache__" not in p.parts
    and "tests" not in p.parts
    and "patches" not in p.parts
)


def _meta(doctype):
    return json.loads(MASTERS[doctype].read_text(encoding="utf-8"))


def _field(path, fieldname):
    meta = json.loads(path.read_text(encoding="utf-8"))
    return next(field for field in meta["fields"] if field["fieldname"] == fieldname)


# --- the two vocabulary tables --------------------------------------------------------


@pytest.mark.parametrize("doctype", list(MASTERS))
def test_each_vocabulary_ships_as_a_real_doctype(doctype):
    meta = _meta(doctype)
    folder = MASTERS[doctype].parent

    assert "istable" not in meta, "a vocabulary table is not a child table"
    assert meta["module"] == "Murasalat Office"
    assert meta["title_field"], "a Link field would otherwise show the code instead of the name"
    assert meta["autoname"].startswith("field:"), doctype
    assert meta["allow_rename"] == 0, "renaming a code would orphan every record that stored it"

    assert (folder / f"{folder.name}.py").is_file()
    assert (folder / f"{folder.name}.js").is_file()


@pytest.mark.parametrize("doctype", list(MASTERS))
def test_the_vocabulary_ships_no_permission_rows(doctype):
    """Access is site configuration, exactly as it is for every other table in this app.

    The consequence is explicit and documented: a System Manager grants read on both tables
    from Desk before users can pick a value in the Link fields. Seeding works without it, since
    master_data registers as an administrator.
    """
    assert not _meta(doctype).get("permissions"), doctype


def test_the_read_grant_a_site_needs_is_written_down():
    docs = (REPO / "docs/ATTACHMENTS.md").read_text(encoding="utf-8")

    assert "Role Permission Manager" in docs, "an undocumented setup step is a broken setup"


@pytest.mark.parametrize("doctype", list(MASTERS))
def test_the_vocabulary_carries_an_arabic_name_and_a_description(doctype):
    label_field = _meta(doctype)["title_field"]
    fields = {field["fieldname"]: field for field in _meta(doctype)["fields"]}

    assert fields[label_field]["reqd"] == 1, doctype
    assert "description" in fields, "a code with no explanation invites a wrong pick"


def test_the_code_and_the_name_are_separate_fields():
    """The code is stored; the name is read. Keeping them apart is what lets a site rename."""
    for doctype in MASTERS:
        meta = _meta(doctype)
        code_field = meta["autoname"].split(":", 1)[1]

        assert code_field != meta["title_field"], doctype


# --- the attachment table now links instead of listing ---------------------------------


def test_the_attachment_type_is_a_link_not_a_frozen_list():
    field = _field(DT / "murasalat_attachment/murasalat_attachment.json", "attachment_type")

    assert field["fieldtype"] == "Link"
    assert field["options"] == "Murasalat Attachment Type"
    assert field["default"] == "Attachment"
    assert field["reqd"] == 1


def test_the_archive_location_replaced_the_free_text_folder():
    meta = json.loads((DT / "murasalat_attachment/murasalat_attachment.json").read_text())
    field = next(f for f in meta["fields"] if f["fieldname"] == "archive_location")

    assert field["fieldtype"] == "Link"
    assert field["options"] == "Murasalat Archive Location"
    assert not field.get("reqd"), "an empty location is honest; an invented one is not"
    assert "folder" not in [f["fieldname"] for f in meta["fields"]]
    assert "folder" not in meta["field_order"]


def test_no_app_file_still_reaches_for_the_old_folder_field():
    """The field collided with Frappe's own folder concept; the name must not come back."""
    offenders = []

    for path in APP_SOURCES:
        source = path.read_text(encoding="utf-8", errors="ignore")
        if '"folder"' in source or "'folder'" in source:
            offenders.append(str(path.relative_to(ROOT)))

    assert offenders == [], offenders


def test_every_seeded_type_is_a_plain_code():
    """The vocabulary is data, so it must not be spelled out anywhere else in the code."""
    source = MASTER_DATA.read_text(encoding="utf-8")
    block = source.split("ATTACHMENT_TYPES = [", 1)[1].split("\n]", 1)[0]
    codes = re.findall(r'"attachment_type": "([^"]+)"', block)

    assert "Main Letter" in codes, "a code already stored on records must keep resolving"
    assert "Attachment" in codes, "the field default points at it"
    assert "Reply" in codes
    assert len(codes) == len(set(codes)), "a duplicated code would seed twice"


def test_the_default_type_is_seeded():
    source = MASTER_DATA.read_text(encoding="utf-8")
    assert '("Murasalat Attachment Type", "Attachment")' in source


def test_the_seeded_locations_are_places_a_small_office_has():
    source = MASTER_DATA.read_text(encoding="utf-8")
    block = source.split("ARCHIVE_LOCATIONS = [", 1)[1].split("\n]", 1)[0]
    codes = re.findall(r'"location": "([^"]+)"', block)

    assert len(codes) >= 3, "one location would not be a vocabulary"
    assert len(codes) == len(set(codes))


# --- what the framework now does instead of us -----------------------------------------


def test_the_duplicate_row_check_is_gone():
    """Frappe already refuses the same content on the same document, by content hash.

    ``File.validate_duplicate_entry`` filters content_hash + is_private + attached_to_doctype +
    attached_to_name, and ``File.has_permission`` defers to the parent record. Both are stronger
    than a comparison of file paths, and neither is ours to maintain.
    """
    production = [
        p for p in ROOT.rglob("*.py")
        if "__pycache__" not in p.parts and "tests" not in p.parts
    ]

    assert production, "the scan found nothing to check"
    for path in production:
        assert "validate_attachment_rows" not in path.read_text(encoding="utf-8", errors="ignore"), path


def test_the_seal_still_covers_the_whole_attachment_set():
    source = RECORDS.read_text(encoding="utf-8")

    assert '"attachments": [' in source
    assert '"linked_files": _linked_file_snapshot(doc)' in source
    assert 'getattr(row, "archive_location", None)' in source


def test_the_child_doctype_really_declares_what_the_seal_reads():
    """The seal reads archive_location defensively, so the name has to be guarded here."""
    meta = json.loads((DT / "murasalat_attachment/murasalat_attachment.json").read_text())
    assert "archive_location" in [f["fieldname"] for f in meta["fields"]]


def test_a_secret_attachment_says_what_it_does_and_does_not_do():
    field = _field(DT / "murasalat_attachment/murasalat_attachment.json", "is_secret")
    description = field.get("description", "")

    assert "File permissions" in description, "hiding a name is not the same as denying access"


# --- the migration ----------------------------------------------------------------------


def test_the_patches_run_in_the_order_the_rename_needs():
    text = PATCHES.read_text(encoding="utf-8")

    assert "[pre_model_sync]" in text and "[post_model_sync]" in text

    # Read the headers as lines, so a comment that mentions a section is not mistaken for one.
    pre = text.split("\n[pre_model_sync]\n", 1)[1].split("\n[post_model_sync]\n", 1)[0]
    post = text.split("\n[post_model_sync]\n", 1)[1]

    assert "murasalat_office.patches.v0_24_rename_attachment_folder" in pre, (
        "the rename needs the old column to still be the only one"
    )
    assert "murasalat_office.patches.v0_25_attachment_vocabulary" in post, (
        "seeding a master table needs the schema to exist"
    )
    assert "murasalat_office.patches.v0_26_index_record_attachments" in post, (
        "the backfill writes Link values, so the vocabulary must be seeded first"
    )
    assert post.index("v0_25_attachment_vocabulary") < post.index("v0_26_index_record_attachments")


def test_the_legacy_patches_kept_their_exact_line():
    """The line is the key in the Patch Log; rewriting it would run the patch again."""
    text = PATCHES.read_text(encoding="utf-8")

    assert "execute:murasalat_office.patches.v0_21_migrate_referrals.execute" in text
    assert "execute:murasalat_office.patches.v0_22_preserve_referral_history.execute" in text


def test_the_rename_patch_rewrites_the_column_rather_than_dropping_it():
    source = (ROOT / "patches/v0_24_rename_attachment_folder.py").read_text(encoding="utf-8")

    assert "sql_ddl" in source
    assert "change `" in source, "a rename keeps the values; add-and-drop would not"
    assert "drop column" not in source.lower(), "the values must move, not disappear"
    assert "has_column" in source, "re-running must be harmless"
    assert "information_schema" in source, "the column type is read, not guessed"


def test_the_vocabulary_patch_reports_before_it_changes_anything():
    source = (ROOT / "patches/v0_25_attachment_vocabulary.py").read_text(encoding="utf-8")

    assert "master_data.seed()" in source
    assert "cleared:" in source and "reset:" in source, "every change is printed"


def test_the_vocabulary_patch_explains_the_clear_rule():
    """A Link field is validated on save, so a dangling value would block the next save."""
    source = (ROOT / "patches/v0_25_attachment_vocabulary.py").read_text(encoding="utf-8")

    assert "not a known location" in source
    assert "DEFAULT_TYPE" in source


def test_every_role_can_read_the_vocabulary_it_has_to_pick_from():
    """A Link field cannot resolve a record the user may not read.

    Found by reviewing launch readiness end to end: the permission plan granted the transaction
    DocTypes but not the two vocabulary tables, so a provisioned site would have shown a clerk
    an empty attachment-type picker on a required field.

    The plan is assembled at import time - the literal plus a merge of VOCABULARY_READ - so the
    test replays that same merge against the shipped source and asserts the result, rather than
    reading either half on its own.
    """
    import ast

    tree = ast.parse((ROOT / "setup/governance_plan.py").read_text(encoding="utf-8"))

    def literal(name):
        for node in tree.body:
            if isinstance(node, ast.Assign) and any(
                isinstance(target, ast.Name) and target.id == name for target in node.targets
            ):
                return ast.literal_eval(node.value)
        raise AssertionError(f"{name} is not declared in governance_plan.py")

    plan = literal("PERMISSION_PLAN")
    vocabulary = literal("VOCABULARY_READ")

    assert plan, "the permission plan is empty"
    assert set(vocabulary) == {"Murasalat Attachment Type", "Murasalat Archive Location"}

    # the same merge the module performs on itself
    for doctypes in plan.values():
        for table, rights in vocabulary.items():
            doctypes.setdefault(table, dict(rights))

    for role, doctypes in plan.items():
        for table in vocabulary:
            assert table in doctypes, (role, table)
            assert doctypes[table].get("read"), (role, table)


def test_the_vocabulary_grant_is_merged_rather_than_repeated():
    """One declaration, applied to every role - so a new role cannot forget it."""
    source = (ROOT / "setup/governance_plan.py").read_text(encoding="utf-8")

    assert "VOCABULARY_READ = {" in source
    assert "for _role_plan in PERMISSION_PLAN.values():" in source
    assert "_role_plan.setdefault(_vocabulary" in source
