"""The attachments panel and the attachments table stay in step.

Frappe has one way to attach a file to a document - a File row carrying
``attached_to_doctype`` and ``attached_to_name`` - and the form's panel, drag-and-drop, the
REST endpoint and a row's own Attach control all go through it. A File event files a
record-level upload in the table (see ``test_attachment_native_index.py``). These tests cover
the other half: the form has to learn about the row it never created.

That half is not cosmetic. ``Document.update_child_table`` deletes every child row the
submitted document does not contain, so a form that never learned about the row would erase
it on the next save. The merge is therefore executed here, not merely read.
"""
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DOCTYPE_DIR = ROOT / "murasalat_office/doctype"

FORMS = {
    "Murasalat Correspondence": DOCTYPE_DIR / "murasalat_correspondence/murasalat_correspondence.js",
    "Murasalat Referral": DOCTYPE_DIR / "murasalat_referral/murasalat_referral.js",
}

MERGE_FUNCTION = re.compile(
    r"function murasalat_merge_attachment_rows\(current, incoming\) \{.*?\n\}\n", re.S
)

NODE = shutil.which("node")
needs_node = pytest.mark.skipif(NODE is None, reason="node is not installed")


def _script(doctype):
    return FORMS[doctype].read_text(encoding="utf-8")


def _block(doctype):
    script = _script(doctype)
    return script[script.index("function murasalat_attachment_rules"):]


def _run_merge(current, incoming):
    """Execute the shipped function itself, so the test cannot drift from the code."""
    function = MERGE_FUNCTION.search(_script("Murasalat Correspondence"))
    assert function, "murasalat_merge_attachment_rows is gone"

    program = "%s\nconsole.log(JSON.stringify(murasalat_merge_attachment_rows(%s, %s)));" % (
        function.group(0),
        json.dumps(current),
        json.dumps(incoming),
    )
    done = subprocess.run([NODE, "-e", program], capture_output=True, text=True)

    assert done.returncode == 0, done.stderr
    return json.loads(done.stdout)


# --- the hook the panel actually fires ----------------------------------------------


@pytest.mark.parametrize("doctype", list(FORMS))
def test_the_panel_upload_method_is_wrapped_and_delegated_to(doctype):
    """`attachment_uploaded` is what the panel runs for every completed upload."""
    block = _block(doctype)

    assert "frm.attachments.attachment_uploaded = function" in block, doctype
    assert "native_attachment_uploaded.call(this, attachment)" in block, (
        "the framework's own method must still run: " + doctype
    )


@pytest.mark.parametrize("doctype", list(FORMS))
def test_the_form_does_not_hook_on_success(doctype):
    """It would never fire.

    ``frappe/public/js/frappe/form/sidebar/attachments.js`` hands
    ``frappe.ui.FileUploader`` its own ``on_success`` - which calls
    ``this.attachment_uploaded`` - and never reads one set on the control.
    """
    assert "on_success" not in _block(doctype), doctype


@pytest.mark.parametrize("doctype", list(FORMS))
def test_the_form_never_reloads_the_document_after_an_upload(doctype):
    """A reload would discard whatever the user had typed but not saved."""
    assert "reload_doc" not in _block(doctype), doctype


@pytest.mark.parametrize("doctype", list(FORMS))
def test_both_forms_carry_the_same_merge(doctype):
    function = MERGE_FUNCTION.search(_script(doctype))
    assert function, doctype
    assert function.group(0) == MERGE_FUNCTION.search(_script("Murasalat Referral")).group(0)


# --- what the merge does -------------------------------------------------------------


@needs_node
def test_a_row_the_server_just_added_is_brought_in():
    rows = _run_merge([], [{"name": "att-2", "file": "/files/b.pdf", "attachment_type": "Attachment"}])

    assert [row["name"] for row in rows] == ["att-2"]
    assert rows[0]["attachment_type"] == "Attachment"


@needs_node
def test_a_row_the_user_has_not_saved_yet_is_kept():
    """An unsaved row carries no server name, so nothing may drop it."""
    rows = _run_merge(
        [{"name": "att-1", "file": "/files/a.pdf"}, {"file": "/files/mine.pdf", "folder": "dfs"}],
        [{"name": "att-1", "file": "/files/a.pdf"}, {"name": "att-2", "file": "/files/b.pdf"}],
    )

    assert [row.get("name") for row in rows] == ["att-1", None, "att-2"]
    assert rows[1]["folder"] == "dfs", "the user's own row is left untouched"


@needs_node
def test_a_file_already_listed_is_not_added_twice():
    rows = _run_merge(
        [{"file": "/files/a.pdf"}],
        [{"name": "att-1", "file": "/files/a.pdf"}],
    )

    assert len(rows) == 1, "the same file under the same row is not duplicated"


@needs_node
def test_a_serverside_row_does_not_arrive_looking_new():
    """`__islocal` would make the next save insert the row a second time."""
    rows = _run_merge([], [{"name": "att-1", "file": "/files/a.pdf", "__islocal": 1}])

    assert "__islocal" not in rows[0]
    assert rows[0]["name"] == "att-1"


@needs_node
def test_a_form_already_in_step_gains_nothing():
    rows = _run_merge(
        [{"name": "att-1", "file": "/files/a.pdf"}],
        [{"name": "att-1", "file": "/files/a.pdf"}],
    )

    assert len(rows) == 1
