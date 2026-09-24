"""Operational notifications: the ten cases, on the framework's own mechanism.

There is no Frappe runtime where these branches were written, so nothing here sends a
notification. What these tests do instead is execute the parts that decide behaviour - the two
Notification conditions and the three Assignment Rule conditions - against documents built to
match each case, and hold the configuration to the shape the framework's own code requires:

* a Days Before / Days After Notification must name its date field, or ``Notification.validate``
  throws;
* the recipients are resolved from the open ToDo rows, so a reminder cannot outlive the
  responsibility it belongs to;
* an Assignment Rule condition is evaluated with the document alone in its namespace
  (``AssignmentRule.safe_eval`` -> ``frappe.safe_eval(condition, None, doc)``), so it may not
  reach for ``frappe`` - while a Notification condition must, to see whether it has fired yet.
"""
import ast
import csv
import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "setup/notifications.py").read_text(encoding="utf-8")
HOOKS = (ROOT / "hooks.py").read_text(encoding="utf-8")
TRANSLATIONS = ROOT / "translations/ar.csv"

sys.path.insert(0, str(ROOT.parent))


def _ensure_frappe():
    """A framework-light stub: this app's notifications module imports frappe, nothing more."""
    module = sys.modules.get("frappe")
    if module is None:
        module = types.ModuleType("frappe")
        sys.modules["frappe"] = module
    module._ = getattr(module, "_", lambda text, *a, **kwargs: text)
    module.throw = getattr(module, "throw", lambda *a, **kwargs: None)
    module.get_doc = getattr(module, "get_doc", lambda *a, **kwargs: None)
    db = getattr(module, "db", None) or types.SimpleNamespace()
    for name, default in (
        ("exists", lambda *a, **k: False),
        ("get_value", lambda *a, **k: None),
        ("set_value", lambda *a, **k: None),
    ):
        setattr(db, name, getattr(db, name, default))
    module.db = db
    return module


_ensure_frappe()
from murasalat_office.setup import notifications  # noqa: E402

REMINDERS = notifications.REMINDERS
RULE = notifications.ASSIGNMENT_RULE


class _Doc:
    """A document as a condition sees it: attributes, and ``.get`` for the rule's own use."""

    def __init__(self, **fields):
        self.__dict__.update(fields)

    def get(self, key, default=None):
        return self.__dict__.get(key, default)


def _fires(condition, already_notified=False, **fields):
    """Evaluate one condition exactly as the framework does: `doc` and `frappe` in scope."""
    frappe = types.SimpleNamespace(
        db=types.SimpleNamespace(exists=lambda *a, **k: already_notified)
    )
    return bool(eval(condition, {"doc": _Doc(**fields), "frappe": frappe}))  # noqa: S307


def _condition(reminder):
    return notifications.reminder_condition(reminder, reminder["name"])


OPEN = dict(
    name="MR-00001",
    workflow_state="Sent",
    due_date="2026-09-30",
    cancelled_on=None,
    recipient_type="User",
    recipient_user="clerk@example.com",
)


@pytest.mark.parametrize("reminder", REMINDERS, ids=[r["name"] for r in REMINDERS])
def test_the_reminder_is_the_frameworks_date_mechanism(reminder):
    """Days Before / Days After is what `trigger_daily_alerts` runs, once a day, natively."""
    assert reminder["event"] in ("Days Before", "Days After")
    assert reminder["days_in_advance"] == 1, "one day of lead time, and one day of grace"


@pytest.mark.parametrize("reminder", REMINDERS, ids=[r["name"] for r in REMINDERS])
def test_the_reminder_declares_the_date_field_the_framework_demands(reminder):
    """`Notification.validate` throws for Days Before/After without a date field."""
    definition = notifications._definition(reminder, reminder["name"])

    assert definition["document_type"] == "Murasalat Referral"
    assert definition["date_changed"] == "due_date"
    assert definition["enabled"] == 1
    assert definition["channel"] == "System Notification"


@pytest.mark.parametrize("reminder", REMINDERS, ids=[r["name"] for r in REMINDERS])
def test_the_recipient_is_whoever_holds_the_work_right_now(reminder):
    """`send_to_all_assignees` resolves the recipients from the Open ToDo rows.

    That is what makes a reminder stop when the responsibility ends. A recipient field would
    keep reminding a user who was unassigned, and a role recipient would remind every holder of
    the role - both ruled out by the brief.
    """
    definition = notifications._definition(reminder, reminder["name"])

    assert definition["send_to_all_assignees"] == 1
    assert definition["recipients"] == [], "no role-wide and no field-based recipient rows"
    assert "receiver_by_role" not in SOURCE


def test_the_assignment_is_the_frameworks_own_assignment_rule():
    assert RULE["document_type"] == "Murasalat Referral"
    assert RULE["rule"] == "Based on Field"
    assert RULE["field"] == "recipient_user", "the referral names the person who owes the work"
    assert RULE["due_date_based_on"] == "due_date"
    assert RULE["disabled"] == 0


def test_nothing_was_built_that_the_framework_already_has():
    """No notification doctype, no scheduler, no queue, no transport."""
    assert "scheduler_events" not in HOOKS, "the framework already runs trigger_daily_alerts"
    assert "Notification Log" not in HOOKS
    assert '"doctype": "Notification Log"' not in SOURCE
    assert "new_doc(" not in SOURCE
    assert "sendmail" not in SOURCE and "whatsapp" not in SOURCE.lower()

    doctypes = [p.name for p in (ROOT / "murasalat_office/doctype").iterdir() if p.is_dir()]
    assert not [name for name in doctypes if "notification" in name]


def test_no_second_notification_is_created_for_an_assignment():
    """Frappe's `assign_to._add` writes the ToDo and its own "Assignment" Notification Log.

    So the two reminders cover only dates - the one event the framework does not already
    announce. A "New" or "Save" rule here would be the duplicate the brief forbids.
    """
    assert {r["event"] for r in REMINDERS} == {"Days Before", "Days After"}
    assert not [r for r in REMINDERS if "assign" in r["name"].lower()]


@pytest.mark.parametrize("reminder", REMINDERS, ids=[r["name"] for r in REMINDERS])
def test_case_1_and_2_open_dated_and_not_yet_reminded_fires(reminder):
    assert _fires(_condition(reminder), **OPEN) is True


@pytest.mark.parametrize("reminder", REMINDERS, ids=[r["name"] for r in REMINDERS])
def test_case_3_a_referral_without_a_due_date_never_fires(reminder):
    """The framework matches the date field exactly, so NULL cannot match - and the condition
    says so too, in case a site ever changes the mechanism."""
    assert _fires(_condition(reminder), **{**OPEN, "due_date": None}) is False


@pytest.mark.parametrize("reminder", REMINDERS, ids=[r["name"] for r in REMINDERS])
def test_case_4_and_5_the_state_decides_that_someone_owes_the_work(reminder):
    assert _fires(_condition(reminder), **{**OPEN, "workflow_state": "Received"}) is True
    assert _fires(_condition(reminder), **{**OPEN, "workflow_state": "Draft"}) is False, (
        "a draft has not been sent, so nobody owes anything yet"
    )


@pytest.mark.parametrize("reminder", REMINDERS, ids=[r["name"] for r in REMINDERS])
def test_case_6_completing_before_the_due_date_stops_the_reminders(reminder):
    """The Assignment Rule's close condition is what ends them: once the ToDo is closed,
    `get_assignees` returns nobody and the notification has no recipient left at all."""
    assert _fires(_condition(reminder), **{**OPEN, "workflow_state": "Completed"}) is False
    assert _fires(_condition(reminder), **{**OPEN, "workflow_state": "Cancelled"}) is False
    assert _fires(_condition(reminder), **{**OPEN, "cancelled_on": "2026-09-25 10:00:00"}) is False


@pytest.mark.parametrize("reminder", REMINDERS, ids=[r["name"] for r in REMINDERS])
def test_case_7_a_late_referral_that_is_then_completed_stops(reminder):
    assert _fires(_condition(reminder), **OPEN) is True
    assert _fires(_condition(reminder), **{**OPEN, "workflow_state": "Completed"}) is False


@pytest.mark.parametrize("reminder", REMINDERS, ids=[r["name"] for r in REMINDERS])
def test_case_9_a_second_run_of_the_same_days_job_writes_nothing(reminder):
    """The guard is the Notification Log lookup inside the condition - no code, no counter."""
    assert _fires(_condition(reminder), already_notified=True, **OPEN) is False


@pytest.mark.parametrize("reminder", REMINDERS, ids=[r["name"] for r in REMINDERS])
def test_case_8_the_message_carries_nothing_from_the_parent_record(reminder):
    """Nothing checks that a recipient can read the record before a log is written for them.

    The framework scopes the log to its `for_user`, not to the document, so the payload is the
    only thing standing between a stale assignee and the parent correspondence. It names the
    referral and its date - never the correspondence, its subject or its body.
    """
    payload = f"{reminder['subject']} {reminder['title']} {reminder['message']}"
    payload = payload.replace("{{ doc.name }}", "MR-00001")
    payload = payload.replace("{{ doc.due_date }}", "2026-09-30")

    for forbidden in ("doc.correspondence", "doc.notes", "doc.instructions"):
        assert forbidden not in payload
    assert "MR-00001" in payload


def test_case_10_two_reminders_per_referral_stay_distinguishable():
    """At most two reminders in a referral's life, each with its own headline and its own
    duplicate-guard key."""
    titles = [r["title"] for r in REMINDERS]
    conditions = [_condition(r) for r in REMINDERS]

    assert len(set(titles)) == len(REMINDERS)
    assert len(set(conditions)) == len(REMINDERS), "each reminder guards on its own log entry"
    assert all(repr(r["title"]) in c for r, c in zip(REMINDERS, conditions))


@pytest.mark.parametrize("reminder", REMINDERS, ids=[r["name"] for r in REMINDERS])
def test_the_notification_condition_is_valid_python(reminder):
    """`evaluate_alert` throws on a condition it cannot evaluate - on a scheduler run."""
    compile(_condition(reminder), "<notification condition>", "eval")


@pytest.mark.parametrize("field", ["assign_condition", "unassign_condition", "close_condition"])
def test_the_assignment_rule_conditions_are_valid_python(field):
    compile(RULE[field], "<assignment rule condition>", "eval")


@pytest.mark.parametrize("field", ["assign_condition", "unassign_condition", "close_condition"])
def test_the_assignment_rule_conditions_never_reach_for_frappe(field):
    """`AssignmentRule.safe_eval` passes the document alone: `frappe` is not in scope there."""
    assert "frappe." not in RULE[field]


def test_the_assignment_rule_assigns_once_and_only_while_the_work_is_owed():
    """The framework calls `apply_assign` only when nothing is assigned, so an unchanged
    referral cannot announce itself twice - and a finished one is never assigned again."""
    assert _fires(RULE["assign_condition"], **OPEN) is True
    assert _fires(RULE["assign_condition"], **{**OPEN, "workflow_state": "Received"}) is True
    assert _fires(RULE["assign_condition"], **{**OPEN, "workflow_state": "Completed"}) is False
    assert _fires(RULE["assign_condition"], **{**OPEN, "workflow_state": "Draft"}) is False
    assert _fires(
        RULE["assign_condition"], **{**OPEN, "recipient_type": "Department", "recipient_user": None}
    ) is False, (
        "a department-targeted referral names no person, and the brief forbids notifying a whole "
        "department - Murasalat Inbox is what tells a department what is waiting"
    )

    assert _fires(RULE["close_condition"], **{**OPEN, "workflow_state": "Completed"}) is True
    assert _fires(RULE["unassign_condition"], **{**OPEN, "workflow_state": "Cancelled"}) is True
    assert _fires(RULE["close_condition"], **OPEN) is False


def test_plan_reads_and_does_not_write():
    """A report a person runs to check a site must not configure it."""
    tree = ast.parse(SOURCE)
    plan = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "plan"
    )

    calls = [
        node.func.attr for node in ast.walk(plan)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    ]
    assert "insert" not in calls
    assert "set_value" not in calls
    assert "get_doc" not in calls


def test_the_native_assignment_notice_is_translated():
    """The assignment notification is Frappe's own text, translated through the app's own
    catalogue - which is how a native message becomes Arabic without a line of code."""
    translated = {
        row[0] for row in csv.reader(TRANSLATIONS.read_text(encoding="utf-8").splitlines())
        if len(row) == 3
    }

    for source_string in (
        "{0} assigned a new task {1} {2} to you",
        "Your assignment on {0} {1} has been removed by {2}",
        "Assignment for {0} {1}",
        "Murasalat Referral",
    ):
        assert source_string in translated, source_string


def test_the_definitions_are_reachable_from_the_provisioner():
    source = (ROOT / "setup/provision.py").read_text(encoding="utf-8")

    assert "notifications.install()" in source
    assert "notifications.plan()" in source
