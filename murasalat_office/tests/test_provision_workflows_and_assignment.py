"""The launch defects found once provisioning finally ran to the end, and the ones behind those.

install-app on health16test.com printed "ok provision" while everything had failed, because
setup/install.py only read its own report and the runners record failures inside theirs. With that
fixed, the console showed the real messages, one after another:

    roles: For Correspondence Supervisor at level 0 in Murasalat Correspondence in row 3:
           Cannot set Assign Amend if not Submittable
    roles: ... Cannot set import as DocType (Murasalat Correspondence) is not importable
    Murasalat Correspondence Lifecycle: None of allow_edit exists on Workflow Transition.
           Available fields: action, allow_self_approval, allowed, condition, ...

Each is verified against Frappe 16:

1. `Workflow Document State.state` is a Link to `Workflow State`, and Frappe throws
   "<state> not a valid State" for one that does not exist - so a Workflow cannot be inserted
   before its States. Nothing created them.
2. `Assignment Rule.assignment_days` is required, and the rule was inserted without it.
3. `provision.readiness` read `workflow_task_readiness()` as a dict while it returns a list of
   checks, so it printed "could not read (list object has no attribute get)".
4. `setup.install` never surfaced the failures a runner recorded in its own report.
5. `allow_edit` exists only on `Workflow Document State`; a `Workflow Transition` carries
   `allowed`. The builder read `allow_edit` off the transition's meta and set it on both rows.
6. The permission plan asked for `import` and `amend`, and Frappe refuses both unless the DocType
   carries `allow_import` / `is_submittable` (doctype.py: check_if_importable, check_if_submittable).

These tests read the shipped source and exercise the pure helpers with a placeholder `frappe`.
"""
import ast
import pathlib
import sys
import types
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
_placeholder = types.ModuleType("frappe")
_placeholder._ = lambda text, *args, **kwargs: text
_placeholder.throw = lambda message, *args, **kwargs: (_ for _ in ()).throw(RuntimeError(message))
sys.modules.setdefault("frappe", _placeholder)

PROVISION = (ROOT / "setup/provision.py").read_text(encoding="utf-8")
NOTIFICATIONS = (ROOT / "setup/notifications.py").read_text(encoding="utf-8")
INSTALL = (ROOT / "setup/install.py").read_text(encoding="utf-8")


def _module(source, name):
    """Execute a setup module with a placeholder frappe and return its namespace."""
    namespace = {"__name__": name}
    exec(compile(ast.parse(source), name, "exec"), namespace)
    return namespace


def _constants(source):
    """Module-level simple assignments, evaluated in source order.

    WORKFLOWS names its roles by constant (CLERK, SUPERVISOR), so ast.literal_eval cannot read it.
    """
    namespace = {}
    for node in ast.parse(source).body:
        if not isinstance(node, ast.Assign) or not isinstance(node.targets[0], ast.Name):
            continue
        try:
            namespace[node.targets[0].id] = eval(
                compile(ast.Expression(node.value), "<constants>", "eval"), {}, namespace
            )
        except Exception:
            continue
    return namespace


def _workflows():
    workflows = _constants(PROVISION).get("WORKFLOWS")
    if not workflows:
        raise AssertionError("WORKFLOWS is not declared in provision.py")
    return workflows


class TestWorkflowStates(unittest.TestCase):
    def test_the_states_are_derived_from_the_workflows(self):
        """A state list written twice drifts; the Workflows are the one source."""
        provision = _module(PROVISION, "provision")
        expected = []
        for spec in _workflows():
            for state in spec["states"]:
                if state["state"] not in expected:
                    expected.append(state["state"])
        self.assertEqual(provision["_required_states"](), expected)
        self.assertIn("Sealed", expected)

    def test_the_states_are_created_before_any_workflow(self):
        body = PROVISION.split("def apply(confirm=False):", 1)[1]
        self.assertIn('_section(report, "workflow_states"', body)
        self.assertLess(
            body.index('_section(report, "workflow_states"'),
            body.index("for spec in WORKFLOWS:"),
            "a Workflow cannot reference a Workflow State that does not exist yet",
        )

    def test_the_states_are_created_through_the_vocabulary_module(self):
        """The creation and the appearance live in setup/workflow_vocabulary.py."""
        vocabulary = (ROOT / "setup/workflow_vocabulary.py").read_text(encoding="utf-8")
        self.assertIn("def ensure_states(states):", vocabulary)
        self.assertIn("frappe.db.exists(WORKFLOW_STATE, state)", vocabulary)
        for forbidden in ("delete_doc", "db.delete", "rename_doc"):
            self.assertNotIn(forbidden, vocabulary)
        self.assertIn("workflow_vocabulary.ensure_states(_required_states())", PROVISION)
        self.assertIn("workflow_vocabulary.ensure_actions(_required_actions())", PROVISION)

    def test_the_actions_are_created_before_any_workflow(self):
        body = PROVISION.split("def apply(confirm=False):", 1)[1]
        self.assertIn('_section(report, "workflow_actions"', body)
        self.assertLess(body.index('_section(report, "workflow_actions"'),
                        body.index("for spec in WORKFLOWS:"))


class TestWorkflowFieldsAreReadFromTheRightTable(unittest.TestCase):
    def setUp(self):
        self.builder = PROVISION.split("def _ensure_workflow(spec, names):", 1)[1]
        self.builder = self.builder.split("def apply(confirm=False):", 1)[0]
        self.loop = self.builder.split('for transition in spec["transitions"]:', 1)[1]

    def test_allow_edit_is_read_from_the_state_table(self):
        """The third launch message: "None of allow_edit exists on Workflow Transition"."""
        self.assertIn('allow_edit = _field(state_meta, "allow_edit")', self.builder)
        self.assertNotIn('_field(transition_meta, "allow_edit")', self.builder)

    def test_a_transition_sets_allowed_and_never_allow_edit(self):
        self.assertIn("row.set(t_allowed", self.loop)
        self.assertNotIn("allow_edit", self.loop)

    def test_each_transition_fieldname_is_resolved_against_the_transition_meta(self):
        for field in ("state", "action", "next_state", "allowed"):
            self.assertIn('_field(transition_meta, "%s")' % field, self.builder)


class TestAssignmentRule(unittest.TestCase):
    WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    def _document(self, fieldtype, options=None):
        notifications = _module(NOTIFICATIONS, "notifications")
        weekdays = list(self.WEEKDAYS)
        blank = chr(10)

        class Field:
            def __init__(self, ftype, opts):
                self.fieldtype = ftype
                self.options = opts

        class Meta:
            name = "Assignment Rule"
            fields = []

            def get_field(self, name):
                return Field(fieldtype, options) if name == "assignment_days" else None

        class ChildMeta:
            name = "Assignment Rule Day"

            def get_field(self, name):
                if name != "day":
                    return None
                return Field("Select", blank.join(weekdays))

        notifications["frappe"].get_meta = lambda doctype: (
            Meta() if doctype == "Assignment Rule" else ChildMeta()
        )
        return notifications["_assignment_rule_document"]()

    def test_a_table_field_gets_one_row_per_offered_day(self):
        document = self._document("Table", "Assignment Rule Day")
        self.assertEqual([row["day"] for row in document["assignment_days"]], self.WEEKDAYS)

    def test_the_days_come_from_the_field_options_not_a_hardcoded_list(self):
        document = self._document("Table", "Assignment Rule Day")
        self.assertEqual(len(document["assignment_days"]), 7)
        source = NOTIFICATIONS.split("def _assignment_rule_document():", 1)[1]
        self.assertIn("get_field(day_field).options", source)

    def test_an_integer_field_gets_a_count(self):
        self.assertEqual(self._document("Int")["assignment_days"], 7)

    def test_a_rule_without_days_is_not_reported_as_current(self):
        body = NOTIFICATIONS.split("def _assignment_rule_is_current(", 1)[1].split("def ", 1)[0]
        self.assertIn("assignment_days", body)

    def test_install_builds_the_document_through_the_helper(self):
        self.assertIn("_assignment_rule_document()", NOTIFICATIONS.split("def install():", 1)[1])


class TestInstallSurfacesNestedFailures(unittest.TestCase):
    def test_a_failure_collected_by_a_runner_is_reported(self):
        install = _module(INSTALL, "install")
        report = {
            "created": {
                "provision": {
                    "master_data": None,
                    "workflows": [],
                    "errors": ["Murasalat Correspondence Lifecycle: Draft not a valid State"],
                },
                "report_roles": {"updated": 13, "errors": []},
            },
            "errors": [],
        }
        found = install["_nested_errors"](report)
        self.assertEqual(len(found), 1)
        self.assertIn("provision:", found[0])
        self.assertIn("not a valid State", found[0])

    def test_a_clean_report_produces_nothing(self):
        install = _module(INSTALL, "install")
        self.assertEqual(
            install["_nested_errors"]({"created": {"a": {"errors": []}}, "errors": []}), []
        )

    def test_the_nested_errors_reach_the_console_and_the_log(self):
        self.assertIn("_nested_errors(report)", INSTALL)
        self.assertIn("provisioning step reported a failure", INSTALL)


class TestReadinessReadsTheRealShape(unittest.TestCase):
    def test_it_handles_both_a_list_of_checks_and_a_dict(self):
        body = PROVISION.split("def readiness():", 1)[1]
        self.assertIn("isinstance(wired, dict)", body)
        self.assertIn('get("status")', body)

    def test_it_reports_the_workflow_states(self):
        self.assertIn("workflow states", PROVISION)


if __name__ == "__main__":
    unittest.main()
