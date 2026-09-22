"""Validate the app's own metadata. Standalone, no pytest and no bench required.

Run directly (``python murasalat_office/tests/validate_metadata.py``) or from CI. Exits
non-zero with a report of every problem found. This is the check that catches the class of
mistake that a metadata-only commit makes easy: a report without a client script, a JSON
file that no longer parses, a translation row that lost a column.
"""
import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT
REPORTS = APP / "murasalat_office/report"
REQUIRED_REPORT_KEYS = (
    "doctype",
    "name",
    "report_name",
    "report_type",
    "is_standard",
    "ref_doctype",
    "module",
    "disabled",
)
problems: list[str] = []


def problem(message: str) -> None:
    problems.append(message)


def check_json_files() -> None:
    for path in sorted(APP.rglob("*.json")):
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except Exception as error:  # noqa: BLE001 - the message is the point
            problem(f"{path.relative_to(APP)}: invalid JSON ({error})")


def check_doctypes() -> None:
    for path in sorted(APP.glob("murasalat_office/doctype/*/*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("doctype") != "DocType":
            continue

        name = data.get("name") or path.stem
        for key in ("name", "module", "fields", "field_order"):
            if not data.get(key):
                problem(f"DocType {name}: missing '{key}'")

        fieldnames = [field["fieldname"] for field in data.get("fields", [])]
        for fieldname in data.get("field_order", []):
            if fieldname not in fieldnames:
                problem(f"DocType {name}: field_order names unknown field '{fieldname}'")

        for fieldname in fieldnames:
            if fieldnames.count(fieldname) > 1:
                problem(f"DocType {name}: duplicate field '{fieldname}'")

        for field in data.get("fields", []):
            if field.get("fieldtype") == "Select" and not field.get("options"):
                problem(f"DocType {name}: Select '{field['fieldname']}' has no options")
            if field.get("fieldtype") == "Link" and not field.get("options"):
                problem(f"DocType {name}: Link '{field['fieldname']}' has no target")


def check_reports() -> None:
    folders = [f for f in sorted(REPORTS.iterdir()) if f.is_dir() and f.name != "__pycache__"]

    if not folders:
        problem("no report folders found")

    for folder in folders:
        slug = folder.name
        script = folder / f"{slug}.py"
        client = folder / f"{slug}.js"
        meta = folder / f"{slug}.json"

        for path in (script, client, meta):
            if not path.is_file():
                problem(f"report {slug}: missing {path.name}")

        if not script.is_file() or not meta.is_file():
            continue

        data = json.loads(meta.read_text(encoding="utf-8"))

        for key in REQUIRED_REPORT_KEYS:
            if data.get(key) in (None, ""):
                problem(f"report {slug}: missing '{key}'")

        if data.get("name") != data.get("report_name"):
            problem(f"report {slug}: name and report_name disagree")

        if data.get("report_type") == "Script Report":
            source = script.read_text(encoding="utf-8")
            if not re.search(r"^\s*return\s+\S", source, re.M):
                problem(f"report {slug}: the script never returns a result")
            # The 4th positional value is the chart and the 5th the summary. A summary
            # handed over as the 4th value is silently dropped by the report view.
            if re.search(r"return\s+[\w_]+\(\)?[^,]*,\s*data\s*,\s*None\s*,\s*summary\s*$", source, re.M):
                problem(f"report {slug}: summary passed in the chart position")


def check_translations() -> None:
    path = APP / "translations/ar.csv"
    if not path.is_file():
        problem("translations/ar.csv is missing")
        return

    rows = list(csv.reader(path.read_text(encoding="utf-8").splitlines()))
    seen: dict[tuple[str, str], set[str]] = {}

    for index, row in enumerate(rows[1:], start=2):
        if not any(cell.strip() for cell in row):
            continue
        if len(row) < 2:
            problem(f"ar.csv line {index}: fewer than two columns")
            continue
        source = row[0].strip()
        if not source:
            problem(f"ar.csv line {index}: empty source")
            continue
        context = row[2].strip() if len(row) > 2 else ""
        seen.setdefault((source, context), set()).add(row[1].strip())

    for (source, context), translations in sorted(seen.items()):
        if len(translations) > 1:
            where = f"{source!r}" + (f" in context {context!r}" if context else "")
            problem(f"ar.csv: conflicting translations for {where}: {sorted(translations)}")


def main() -> int:
    check_json_files()
    check_doctypes()
    check_reports()
    check_translations()

    if problems:
        print(f"metadata validation failed with {len(problems)} problem(s):")
        for message in problems:
            print(f"  - {message}")
        return 1

    print("metadata validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
