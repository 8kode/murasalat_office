"""The permission plan is checked against the DocTypes it governs, before it is written.

Found on a launch install: `provision.apply` died on

    For Correspondence Supervisor at level 0 in Murasalat Correspondence in row 3:
    Cannot set Assign Amend if not Submittable

after the roles had been created - and because that step was not isolated, the master data, the
print formats, the notifications and the Workflows were never attempted either. The plan asked
for `amend` on a DocType that is not submittable; Frappe refuses that in
`core/doctype/doctype/doctype.py::check_if_submittable`, while saving the DocType.

An amendment in this application is the Reopen transition, not Frappe's amend. These tests read
the shipped metadata instead of the live site, so they hold in any environment.
"""
import ast
import json
import pathlib
import sys
import types
import unittest

# governance_plan imports frappe; these tests read its source, so a placeholder module does.
sys.modules.setdefault("frappe", types.ModuleType("frappe"))

ROOT = pathlib.Path(__file__).resolve().parents[1]
DOCTYPES = ROOT / "murasalat_office/doctype"

# The native fields of DocPerm / Custom DocPerm (Frappe core, version 16).
NATIVE_RIGHTS = {
    "read", "write", "create", "delete", "submit", "cancel", "amend", "report", "export",
    "import", "share", "print", "email", "if_owner", "select", "mask", "set_user_permissions",
}
SUBMISSION_ONLY = {"submit", "cancel", "amend"}
ROLES = {"Correspondence Clerk", "Correspondence Supervisor", "Correspondence Auditor"}
SUBMISSION_ONLY = {"submit", "cancel", "amend"}
RIGHT_FLAGS = {"submit": "is_submittable", "cancel": "is_submittable", "amend": "is_submittable",
               "import": "allow_import"}


def _source():
    return (ROOT / "setup/governance_plan.py").read_text(encoding="utf-8")


def _plan():
    """PERMISSION_PLAN as data, without importing the module (it imports frappe)."""
    for node in ast.parse(_source()).body:
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "PERMISSION_PLAN" for t in node.targets
        ):
            return ast.literal_eval(node.value)
    raise AssertionError("PERMISSION_PLAN is not declared in governance_plan.py")


def _shipped_doctypes():
    """name -> is_submittable, read from the metadata this app ships."""
    meta = {}
    for path in DOCTYPES.glob("*/*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("doctype") == "DocType":
            meta[data["name"]] = bool(data.get("is_submittable"))
    return meta


class TestPermissionPlan(unittest.TestCase):
    def test_no_right_needs_a_flag_the_doctype_does_not_carry(self):
        """"Cannot set Assign Amend if not Submittable" and "Cannot set import ... is not
        importable" - the two messages that each stopped a launch install at the roles step."""
        flags = {}
        for path in (ROOT / "murasalat_office/doctype").glob("*/*.json"):
            data = json.loads(path.read_text(encoding="utf-8"))
            if data.get("doctype") == "DocType":
                flags[data["name"]] = data
        offenders = []
        for role, doctypes in _plan().items():
            for doctype, rights in doctypes.items():
                for right, flag in RIGHT_FLAGS.items():
                    if rights.get(right) and not (flags.get(doctype) or {}).get(flag):
                        offenders.append(f"{role} on {doctype}: {right} needs {flag}")
        self.assertEqual(offenders, [], "these rights need a DocType flag that is not set: " + str(offenders))

    def test_every_doctype_in_the_plan_is_shipped(self):
        submittable = _shipped_doctypes()
        unknown = sorted({d for rows in _plan().values() for d in rows} - set(submittable))
        self.assertEqual(unknown, [], f"the plan names DocTypes this app does not ship: {unknown}")

    def test_every_right_is_a_native_docperm_field(self):
        invalid = sorted({r for rows in _plan().values() for rights in rows.values() for r in rights}
                         - NATIVE_RIGHTS)
        self.assertEqual(invalid, [], f"not DocPerm fields: {invalid}")

    def test_the_three_roles_are_the_ones_the_app_documents(self):
        self.assertEqual(set(_plan()), ROLES)

    def test_delete_and_share_stay_off_the_sealed_records(self):
        """Deleting a correspondence would destroy the audit trail the app exists to keep."""
        for role, doctypes in _plan().items():
            for record in ("Murasalat Correspondence", "Murasalat Referral"):
                self.assertNotIn("delete", doctypes.get(record, {}), f"{role} on {record}")

    def test_the_guard_reports_a_right_without_its_flag_and_passes_a_clean_plan(self):
        """plan_problems is exercised through its callable, without a site."""
        namespace = {}
        exec(compile(ast.parse(_source()), "<governance_plan>", "exec"), namespace)
        guard = namespace["plan_problems"]
        nothing_set = lambda doctype, flag: False

        namespace["PERMISSION_PLAN"] = {"Correspondence Supervisor": {"Murasalat Correspondence": {"amend": 1}}}
        problems = guard(nothing_set)
        self.assertTrue(problems, "amend without is_submittable must be reported")
        self.assertIn("amend", problems[0])

        namespace["PERMISSION_PLAN"] = {"Correspondence Supervisor": {"Murasalat Correspondence": {"import": 1}}}
        problems = guard(nothing_set)
        self.assertTrue(problems, "import without allow_import must be reported")
        self.assertIn("allow_import", problems[0])

        namespace["PERMISSION_PLAN"] = {"Correspondence Clerk": {"Murasalat Correspondence": {"read": 1}}}
        self.assertEqual(guard(nothing_set), [], "a read right is always fine")

    def test_the_shipped_plan_passes_its_own_guard(self):
        namespace = {}
        exec(compile(ast.parse(_source()), "<governance_plan>", "exec"), namespace)  # noqa: S102
        flags = {}
        for path in (ROOT / "murasalat_office/doctype").glob("*/*.json"):
            data = json.loads(path.read_text(encoding="utf-8"))
            if data.get("doctype") == "DocType":
                flags[data["name"]] = data
        self.assertEqual(
            namespace["plan_problems"](lambda doctype, flag: bool(flags.get(doctype, {}).get(flag))),
            [],
            "the shipped plan must pass its own guard",
        )


class TestProvisioningResilience(unittest.TestCase):
    def setUp(self):
        self.source = (ROOT / "setup/provision.py").read_text(encoding="utf-8")
        self.body = self.source.split("def apply(confirm=False):", 1)[1].split(
            "def _unattached_transitions(", 1)[0]

    def test_every_section_runs_through_the_isolation_helper(self):
        for section in ("master_data", "roles", "print_formats", "notifications"):
            self.assertIn(f'_section(report, "{section}"', self.body, section)

    def test_an_earlier_failure_does_not_remove_a_later_section(self):
        """The exact regression: the roles step died and nothing after it was attempted."""
        self.assertLess(self.body.index('"roles"'), self.body.index('"print_formats"'))
        self.assertLess(self.body.index('"print_formats"'), self.body.index('"notifications"'))
        self.assertIn("_section(report, ", self.body)

    def test_the_failure_is_recorded_and_not_raised(self):
        helper = self.source.split("def _section(report, key, runner):", 1)[1]
        self.assertIn("except Exception", helper)
        self.assertIn('report["errors"].append', helper)


if __name__ == "__main__":
    unittest.main()
