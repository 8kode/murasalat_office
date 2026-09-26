"""A Workflow is only usable if the two name tables it points at are filled.

`Workflow Document State.state` is a Link to Workflow State and `Workflow Transition.action` is a
Link to Workflow Action Master. Frappe validates links when it saves the document, so a Workflow
that names either one and finds no record cannot be inserted at all - and on a fresh site neither
table had a single row. That is the defect this module answers.

These tests read the shipped source and exercise the pure helpers with a placeholder `frappe`.
"""
import ast
import pathlib
import re
import sys
import types
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
_placeholder = types.ModuleType("frappe")
# The module under test does `from frappe import _`, so the placeholder has to carry it - and
# `.throw`, which _field calls when a framework fieldname is missing.
_placeholder._ = lambda text, *args, **kwargs: text
_placeholder.throw = lambda message, *args, **kwargs: (_ for _ in ()).throw(RuntimeError(message))
sys.modules.setdefault("frappe", _placeholder)

VOCABULARY = (ROOT / "setup/workflow_vocabulary.py").read_text(encoding="utf-8")
PROVISION = (ROOT / "setup/provision.py").read_text(encoding="utf-8")

# frappe/frappe/workflow/doctype/workflow_state/workflow_state.json (version 16).
FRAMEWORK_STYLES = {"Primary", "Info", "Success", "Warning", "Danger", "Inverse"}
# frappe/frappe/workflow/doctype/workflow_state/workflow_state.json, the `icon` Select.
FRAMEWORK_ICONS = {
    "edit", "inbox", "lock", "ok-sign", "share", "download", "ok", "ban-circle", "time",
    "ok-circle", "circle-arrow-right",
}


def _namespace(source, name):
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


def _workflow_names():
    constants = _constants(PROVISION)
    states, actions = [], []
    for spec in constants["WORKFLOWS"]:
        for state in spec["states"]:
            if state["state"] not in states:
                states.append(state["state"])
        for transition in spec["transitions"]:
            if transition["action"] not in actions:
                actions.append(transition["action"])
    return states, actions


class TestDerivation(unittest.TestCase):
    def test_the_state_names_come_from_the_workflows(self):
        provision = _namespace(PROVISION, "provision")
        states, _ = _workflow_names()
        self.assertEqual(provision["_required_states"](), states)

    def test_the_action_names_come_from_the_workflows(self):
        provision = _namespace(PROVISION, "provision")
        _, actions = _workflow_names()
        self.assertEqual(provision["_required_actions"](), actions)
        self.assertIn("Register", actions)
        self.assertIn("Return for Amendment", actions)

    def test_both_vocabularies_are_created_before_any_workflow(self):
        body = PROVISION.split("def apply(confirm=False):", 1)[1]
        for section in ("workflow_states", "workflow_actions"):
            self.assertIn('_section(report, "%s"' % section, body)
            self.assertLess(body.index('_section(report, "%s"' % section),
                            body.index("for spec in WORKFLOWS:"))


class TestAppearance(unittest.TestCase):
    def test_every_state_has_an_icon_and_a_colour(self):
        vocabulary = _namespace(VOCABULARY, "workflow_vocabulary")
        states, _ = _workflow_names()
        missing = [state for state in states if state not in vocabulary["STATE_APPEARANCE"]]
        self.assertEqual(missing, [], f"states with no appearance: {missing}")

    def test_the_colours_are_frameworks_own_options(self):
        vocabulary = _namespace(VOCABULARY, "workflow_vocabulary")
        for state, look in vocabulary["STATE_APPEARANCE"].items():
            self.assertIn(look["style"], FRAMEWORK_STYLES, state)

    def test_the_icons_are_names_the_framework_offers(self):
        vocabulary = _namespace(VOCABULARY, "workflow_vocabulary")
        for state, look in vocabulary["STATE_APPEARANCE"].items():
            self.assertRegex(look["icon"], re.compile(r"^[a-z][a-z-]*$"), state)
            self.assertIn(look["icon"], FRAMEWORK_ICONS, state)

    def test_an_unknown_state_still_gets_a_usable_pill(self):
        vocabulary = _namespace(VOCABULARY, "workflow_vocabulary")
        fallback = vocabulary["appearance"]("A State Added Later")
        self.assertEqual(set(fallback), {"icon", "style"})
        self.assertIn(fallback["style"], FRAMEWORK_STYLES)

    def test_cancelled_is_the_only_red_state(self):
        """Red on a status pill means lost; anything else reads as an error to a clerk."""
        vocabulary = _namespace(VOCABULARY, "workflow_vocabulary")
        red = [state for state, look in vocabulary["STATE_APPEARANCE"].items()
               if look["style"] == "Danger"]
        self.assertEqual(red, ["Cancelled"])


class FakeFrappe:
    """The smallest frappe the creators touch: exists, get_meta, get_doc, set_value."""

    def __init__(self, existing=(), records=None):
        self.existing = set(existing)
        self.records = records or {}
        self.created = []
        self.set_values = []
        self.db = self  # frappe.db.exists / frappe.db.set_value

    def exists(self, doctype, name):
        return name in self.existing

    def set_value(self, doctype, name, values, *args, **kwargs):
        self.set_values.append((name, dict(values)))

    def get_meta(self, doctype):
        return Meta(doctype)

    def get_doc(self, doctype, name=None):
        if isinstance(doctype, dict):
            # A new record is passed as a dict: {"doctype": ..., "workflow_state_name": ...}
            return Record(doctype.get("doctype", ""), dict(doctype), self)
        return Record(doctype, self.records.get(name) or {}, self)


class Record(dict):
    def __init__(self, doctype, values, frappe):
        super().__init__(values)
        self.doctype = doctype
        self._frappe = frappe

    def insert(self, **kwargs):
        self._frappe.created.append(dict(self))
        return self


class Field:
    def __init__(self, fieldname):
        self.fieldname = fieldname


class Meta:
    def __init__(self, doctype):
        self.name = doctype

    fields = [Field("workflow_state_name"), Field("icon"), Field("style"),
              Field("workflow_action_name")]

    def get_field(self, name):
        return next((field for field in self.fields if field.fieldname == name), None)


class TestCreation(unittest.TestCase):
    def _vocabulary(self, existing=(), records=None):
        vocabulary = _namespace(VOCABULARY, "workflow_vocabulary")
        fake = FakeFrappe(existing=existing, records=records)
        vocabulary["frappe"] = fake
        return vocabulary, fake

    def test_a_missing_state_is_created_with_its_appearance(self):
        vocabulary, fake = self._vocabulary()
        result = vocabulary["ensure_states"](["Draft"])
        self.assertEqual(fake.created, [{"doctype": "Workflow State",
                                         "workflow_state_name": "Draft",
                                         "icon": "edit", "style": "Inverse"}])
        self.assertEqual(result["created"], ["Draft"])

    def test_an_existing_state_is_not_recreated(self):
        vocabulary, fake = self._vocabulary(
            existing=("Draft",), records={"Draft": {"icon": "star", "style": "Info"}}
        )
        result = vocabulary["ensure_states"](["Draft"])
        self.assertEqual(fake.created, [])
        self.assertEqual(fake.set_values, [], "a chosen appearance must never be rewritten")
        self.assertEqual(result["existing"], ["Draft"])

    def test_a_bare_state_is_styled_but_a_chosen_value_is_kept(self):
        vocabulary, fake = self._vocabulary(
            existing=("Draft",), records={"Draft": {"icon": "", "style": "Danger"}}
        )
        result = vocabulary["ensure_states"](["Draft"])
        self.assertEqual(result["styled"], ["Draft"])
        self.assertEqual(fake.set_values, [("Draft", {"icon": "edit"})],
                         "only the empty field is filled; the chosen colour stays")

    def test_an_action_is_created_when_missing_and_left_when_not(self):
        vocabulary, fake = self._vocabulary(existing=("Register",))
        result = vocabulary["ensure_actions"](["Register", "Send"])
        self.assertEqual(result["created"], ["Send"])
        self.assertEqual(result["existing"], ["Register"])
        self.assertEqual(fake.created, [{"doctype": "Workflow Action Master",
                                         "workflow_action_name": "Send"}])

    def test_nothing_is_deleted_or_renamed(self):
        for forbidden in ("delete_doc", "db.delete", "rename_doc", "delete("):
            self.assertNotIn(forbidden, VOCABULARY)


class TestReadiness(unittest.TestCase):
    def test_the_actions_are_reported(self):
        self.assertIn('"workflow actions"', PROVISION)

    def test_the_vocabulary_plan_reads_only(self):
        body = VOCABULARY.split("def plan(states, actions):", 1)[1]
        self.assertIn("frappe.db.exists", body)
        self.assertNotIn("insert", body)


if __name__ == "__main__":
    unittest.main()
