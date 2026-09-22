"""The Arabic Desk must not fall back to English for app-owned text.

Frappe ships its own Arabic catalogue, so framework terms (Task, Role, Workflow) are its
responsibility. What this pins is the app's own vocabulary — the labels the app's doctypes,
reports and workspace contribute — plus the one misspelling that shipped to users.
"""
import csv
import glob
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

APP_OWNED_LABELS = (
    "Audit & Security",
    "Body",
    "Cancel Reason",
    "Clear Approval",
    "Cancelled By",
    "Cancelled On",
    "Correspondence Register",
    "Draft — Not Sent",
    "Follow-up Queue",
    "Murasalat Correspondence Direction",
    "Originating Department",
    "Referral Aging",
    "Referral Cancelled",
    "Reopen Reason",
    "Sealed",
    "Sealed By",
    "Sealed On",
    "Sender",
    "Stamp Approval",
    "Unsealed",
)


def _rows():
    return list(csv.reader((ROOT / "translations/ar.csv").read_text(encoding="utf-8").splitlines()))


@pytest.mark.parametrize("label", APP_OWNED_LABELS)
def test_every_app_owned_label_has_an_arabic_row(label):
    sources = {row[0].strip() for row in _rows()[1:] if row and row[0].strip()}
    assert label in sources, label


def test_the_translation_file_keeps_its_columns():
    rows = _rows()
    assert rows[0][0].strip() == "source"

    for index, row in enumerate(rows[1:], start=2):
        if not any(cell.strip() for cell in row):
            continue
        assert len(row) >= 2, f"line {index}: {row}"
        if len(row) > 2 and row[2].strip():
            assert len(row) >= 3, f"line {index}: {row}"


def test_no_term_carries_two_different_arabic_strings():
    """Frappe picks one row and silently ignores the other, so a conflict is a defect."""
    conflicts = {}

    for row in _rows()[1:]:
        if not row or not row[0].strip():
            continue
        context = row[2].strip() if len(row) > 2 else ""
        conflicts.setdefault((row[0].strip(), context), set()).add(row[1].strip())

    ambiguous = {key: sorted(values) for key, values in conflicts.items() if len(values) > 1}
    assert ambiguous == {}, ambiguous


def test_the_sidebar_direction_label_is_spelled_correctly():
    """Written as an escape so this file does not itself trip the scan."""
    misspelling = "\u0625\u062a\u062c\u0627\u0629"
    offenders = []

    for pattern in ("**/*.json", "**/*.js", "**/*.csv", "**/*.py", "**/*.html", "**/*.md"):
        for path in glob.glob(str(ROOT / pattern), recursive=True):
            if misspelling in Path(path).read_text(encoding="utf-8", errors="ignore"):
                offenders.append(path)

    assert offenders == [], offenders


def test_the_arabic_workspace_labels_are_present():
    sidebar = (ROOT / "workspace_sidebar/murasalat_office.json").read_text(encoding="utf-8")
    for label in ("سجل المعاملات", "أعمار الإحالات"):
        assert label in sidebar, label
