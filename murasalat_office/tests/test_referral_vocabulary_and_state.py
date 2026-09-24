"""A migrated referral, and the two ways it disagreed with itself.

The record a real site produced showed both at once: its recipient type read
"Organization" - the vocabulary this field offered before it was renamed - and its state read
"Sent" while the panel beside it read "لم تُرسل". Neither is a UI problem, and neither was
visible to a metadata check:

* the vocabulary lived in rows the conversion patch copied verbatim, and nothing re-validated a
  migrated row until a lifecycle action ran the DocType's invariants;
* the panel decided "sent" from the ``sent_on`` timestamp alone, which the child table the row
  came from had no way to carry.

These tests execute the deciding code rather than reading it: the patch's resolver and the
panel's two predicates, lifted out of their modules so no frappe import is needed.
"""
import ast
import csv
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
OVERVIEW = (ROOT / "services/overview.py").read_text(encoding="utf-8")
PATCH = ROOT / "patches/v0_27_legacy_referral_vocabulary.py"
PATCHES = (ROOT / "patches.txt").read_text(encoding="utf-8")
CONTROLLER = (
    ROOT / "murasalat_office/doctype/murasalat_referral/murasalat_referral.py"
).read_text(encoding="utf-8")
TRANSLATIONS = ROOT / "translations/ar.csv"


def _lift(source, names):
    """Execute the named module level defs, and the literals they sit next to, in isolation."""
    tree = ast.parse(source)
    parts = []

    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name in names:
            parts.append(ast.get_source_segment(source, node))
        elif isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id in names for t in node.targets
        ):
            parts.append(ast.get_source_segment(source, node))

    namespace = {}
    exec("\n\n".join(parts), namespace)  # noqa: S102 - lifting our own source, not input
    return namespace


PANEL = _lift(OVERVIEW, {"_is_sent", "_is_completed", "_is_closed_referral"})
PATCH_NS = _lift(PATCH.read_text(encoding="utf-8"), {"target_for", "LEGACY"})


# --- the vocabulary -------------------------------------------------------------------


@pytest.mark.parametrize(
    "row,expected",
    [
        ({"recipient_type": "Organization", "recipient_department": "X"}, "Department"),
        ({"recipient_type": "Organization", "recipient_user": "a@b.c"}, "User"),
        ({"recipient_type": "organization", "recipient_department": "X"}, "Department"),
        ({"recipient_type": "Dept", "recipient_department": "X"}, "Department"),
        ({"recipient_type": "User", "recipient_user": "a@b.c"}, "User"),
        ({"recipient_type": "Department", "recipient_department": "X"}, "Department"),
        # The link is the stronger evidence, and it wins over the stored name.
        ({"recipient_type": "Organization", "recipient_user": "a@b.c",
          "recipient_department": None}, "User"),
        # Nothing to go on: reported, never guessed.
        ({"recipient_type": "Something Else"}, None),
        ({"recipient_type": None}, None),
        ({"recipient_type": "", "recipient_user": "a@b.c",
          "recipient_department": "X"}, None),
    ],
)
def test_the_legacy_recipient_type_is_resolved_or_reported(row, expected):
    assert PATCH_NS["target_for"](row) == expected


def test_the_patch_only_touches_rows_outside_the_declared_vocabulary():
    """It reads a filter, so a healthy row is never even loaded - idempotence by construction."""
    source = PATCH.read_text(encoding="utf-8")

    assert '["not in", list(VALID)]' in source
    assert "update_modified=False" in source, "a repair is not an edit to the record"
    assert "def plan():" in source and "def execute():" in source


def test_the_patch_is_registered_after_the_schema_is_in_place():
    """It reads a column and writes rows, so it belongs in post_model_sync, listed bare."""
    section = PATCHES.split("[post_model_sync]", 1)[1]

    assert "murasalat_office.patches.v0_27_legacy_referral_vocabulary" in section
    assert "execute:murasalat_office.patches.v0_27" not in section, (
        "an execute: line is exec'd without the app name in scope"
    )


def test_the_refusal_names_the_value_it_refused():
    """Without it, an empty field and a vocabulary from an earlier version read the same."""
    assert "this record has {0}" in CONTROLLER
    assert "repr(self.recipient_type)" in CONTROLLER


def test_the_new_refusal_is_translated():
    translated = {
        row[0]
        for row in csv.reader(TRANSLATIONS.read_text(encoding="utf-8").splitlines())
        if len(row) == 3
    }

    assert "Recipient Type must be User or Department; this record has {0}." in translated


# --- the state ------------------------------------------------------------------------


SENT_STATE_ONLY = {"sent_on": None, "completed_on": None, "workflow_state": "Sent"}
RECEIVED_STATE_ONLY = {"sent_on": None, "completed_on": None, "workflow_state": "Received"}
COMPLETED_STATE_ONLY = {"sent_on": None, "completed_on": None, "workflow_state": "Completed"}
CANCELLED_STATE_ONLY = {"sent_on": None, "completed_on": None, "workflow_state": "Cancelled"}
DRAFT = {"sent_on": None, "completed_on": None, "workflow_state": "Draft"}
STAMPED = {"sent_on": "2026-09-01 09:00:00", "completed_on": None, "workflow_state": "Sent"}


def test_a_migrated_sent_referral_reads_as_sent():
    """The exact record from the site: state "Sent", no timestamp, panel said "لم تُرسل"."""
    assert PANEL["_is_sent"](SENT_STATE_ONLY) is True
    assert PANEL["_is_sent"](RECEIVED_STATE_ONLY) is True
    assert PANEL["_is_sent"](COMPLETED_STATE_ONLY) is True


def test_a_draft_still_reads_as_a_draft():
    """The rule must not make every referral look sent - the state has to say so."""
    assert PANEL["_is_sent"](DRAFT) is False
    assert PANEL["_is_sent"]({**DRAFT, "workflow_state": None}) is False
    assert PANEL["_is_sent"]({**DRAFT, "workflow_state": ""}) is False


def test_both_sources_agree_on_a_stamped_record():
    assert PANEL["_is_sent"](STAMPED) is True
    assert PANEL["_is_completed"](STAMPED) is False


def test_completion_reads_from_either_source():
    assert PANEL["_is_completed"](COMPLETED_STATE_ONLY) is True
    assert PANEL["_is_completed"]({**STAMPED, "completed_on": "2026-09-02 10:00:00"}) is True
    assert PANEL["_is_completed"](RECEIVED_STATE_ONLY) is False


def test_cancelled_work_is_closed_not_open():
    """Cancellation ends the work without completing it, so it must leave the open set - the
    same rule the notification close condition and the cancellation transition follow."""
    assert PANEL["_is_closed_referral"](CANCELLED_STATE_ONLY) is True
    assert PANEL["_is_closed_referral"]({**DRAFT, "cancelled_on": "2026-09-20 10:00:00"}) is True
    assert PANEL["_is_closed_referral"](RECEIVED_STATE_ONLY) is False


def test_the_panel_no_longer_decides_from_the_timestamp_alone():
    """Every site that decided sent/open/draft had to be moved onto the two-source rule."""
    source = OVERVIEW

    assert source.count('not row.get("sent_on")') == 0
    assert source.count('bool(doc.sent_on)') == 0
    assert source.count("not doc.sent_on") == 0
    assert source.count("_is_sent(") >= 4, "the kpis, the list rows and the document panel"


def test_the_correspondence_panel_uses_the_same_rule_for_the_seal():
    """A correspondence migrated with state "Sealed" and no seal timestamp must not read as
    unsealed while its badge says otherwise."""
    assert 'doc.workflow_state == "Sealed"' in OVERVIEW


def test_a_list_row_is_not_decorated_from_a_field_it_never_fetched():
    """`decorate_referrals` reads the state, so the query has to select it."""
    block = OVERVIEW.split("REFERRAL_FIELDS = [", 1)[1].split("]", 1)[0]

    assert '"workflow_state"' in block
    assert '"cancelled_on"' in block
