"""Every string the code hands to _() / __() must have an Arabic row.

This guards the gap found in the whole-surface audit: report labels, Desk buttons and
refusal messages were passing through untranslated, so they rendered in English on an
Arabic Desk. Run: python3 -m pytest murasalat_office/tests/test_arabic_coverage.py -q
"""

import ast
import csv
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Frappe renders these itself; our own row is not required.
FRAMEWORK_SUPPLIED = set()

PY_CALL = re.compile(r"^\s*(?:_|__)\(|(?:_|__)\(")
JS_CALL = re.compile(r"(?:^|[^A-Za-z_])(?:_|__)\(\s*([\"'])(.+?)\1\s*\)")


def arabic_rows():
    rows = list(csv.reader((ROOT / "translations/ar.csv").read_text(encoding="utf-8").splitlines()))
    return rows


def code_literals():
    literals = set()
    for path in ROOT.rglob("*.py"):
        if "__pycache__" in str(path) or path.name == "test_arabic_coverage.py":
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = getattr(node.func, "id", None) or getattr(node.func, "attr", None)
                if name in ("_", "__") and node.args:
                    arg = node.args[0]
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                        literals.add(re.sub(r"\s+", " ", arg.value).strip())
    for path in list(ROOT.rglob("*.js")) + list(ROOT.rglob("*.html")):
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            for match in JS_CALL.finditer(line):
                literals.add(re.sub(r"\s+", " ", match.group(2)).strip())
    return {s for s in literals if len(s) > 1 and re.search(r"[A-Za-z]", s)}


class TestArabicCoverage(unittest.TestCase):
    def test_csv_is_three_columns_and_has_no_duplicate_sources(self):
        rows = arabic_rows()
        malformed = [i for i, row in enumerate(rows, 1) if len(row) != 3]
        self.assertEqual(malformed, [], f"malformed ar.csv rows: {malformed}")
        sources = [row[0] for row in rows]
        duplicates = sorted({s for s in sources if sources.count(s) > 1})
        self.assertEqual(duplicates, [], f"duplicate ar.csv sources: {duplicates}")

    def test_every_translated_literal_has_a_row(self):
        available = {row[0] for row in arabic_rows()}
        missing = sorted(s for s in code_literals() - available - FRAMEWORK_SUPPLIED)
        self.assertEqual(
            missing, [],
            "these strings reach the Desk in English (no ar.csv row):\n  " + "\n  ".join(missing),
        )

    def test_arabic_rows_are_populated(self):
        blank = [row[0] for row in arabic_rows() if not row[1].strip()]
        self.assertEqual(blank, [], f"rows without an Arabic translation: {blank}")


if __name__ == "__main__":
    unittest.main()
