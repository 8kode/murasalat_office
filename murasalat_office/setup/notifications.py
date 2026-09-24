"""Operational notifications, assembled from Frappe's own building blocks.

Five questions a user has to be able to answer, and the native surface that answers each:

1. *what arrived* and 2. *what should I do*
       Native **Assignment**: an Assignment Rule assigns a sent, user-targeted referral to
       ``recipient_user``. That creates the framework's own ToDo, its own share when the
       assignee cannot already read the record, and its own Notification Log of type
       "Assignment" - so no second notification is written for the same event.
3. *when must I finish* and 4. *what is late*
       Native **Notification** rows on the framework's Days Before / Days After mechanism,
       driven by the daily ``trigger_daily_alerts`` job and delivered to the in-app bell.
5. *is a formal action waiting for me*
       Nothing added. Frappe's own Workflow Action list already shows the transitions a
       user's role may act on.

There is no notification doctype, no inbox, no queue, no scheduler and no transport in this
module. It creates native rows through Frappe's own models, exactly as clicking through Desk
would - the pattern ``provision.py`` and ``report_print_formats.py`` already use.

Four decisions worth the sentence:

* **Recipients are the assignees, not ``recipient_user``.** A completed referral must stop
  reminding anyone. ``send_to_all_assignees`` resolves the recipients from the Open ToDo rows,
  so responsibility that ended takes its reminders with it - the Assignment Rule's close
  condition is what ends it. ``recipient_user`` would keep reminding a user who is no longer
  responsible, and a role recipient would remind every holder of the role.
* **One day before the due date, one day after.** The framework matches the date field exactly,
  so each reminder fires on a single day and a referral earns at most two reminders in its
  life. ``days_in_advance`` is an Int field: changing the lead time is a Desk edit, not a
  release.
* **The duplicate guard is a condition, not code.** The date match already limits a reminder to
  one day; the condition additionally refuses when a Notification Log of that kind already
  exists for the document, so a second run of the same day's job writes nothing.
* **The message carries the referral's own identity and nothing else.** Nothing checks that a
  recipient can read the record before a Notification Log is written for them - the framework
  scopes the log to its ``for_user``, not to the document. Keeping the parent correspondence's
  subject and body out of the message is what keeps a stale assignee from reading them.

    bench --site <site> execute murasalat_office.setup.notifications.plan
    bench --site <site> execute murasalat_office.setup.notifications.install
"""
import frappe
from frappe import _

REFERRAL = "Murasalat Referral"

# The workflow states in which a referral is somebody's open work, and the ones in which
# nobody owes anything any more. Read from the shipped Workflow in provision.WORKFLOWS; a
# state renamed there has to be renamed here, and ``readiness`` reports the mismatch.
OPEN_STATES = ("Sent", "Received")
DONE_STATES = ("Completed", "Cancelled")

# The condition a reminder must satisfy. Spelled once and reused, so the two reminders cannot
# drift apart.
_OPEN = 'doc.workflow_state in {states} and not doc.cancelled_on'.format(states=OPEN_STATES)
_DONE = 'doc.workflow_state in {states} or doc.cancelled_on'.format(states=DONE_STATES)

REMINDERS = [
    {
        "name": "Murasalat Referral Due Soon",
        "event": "Days Before",
        "days_in_advance": 1,
        # Static headline: it is the duplicate guard's key as well as the bell's category, so
        # it must not depend on the document's values.
        "title": "موعد إحالة يقرب",
        "subject": "الإحالة {{ doc.name }} موعدها {{ doc.due_date }}",
        "message": "إحالة موكولة إليك يقترب موعدها. افتحها لاستلامها أو إتمامها.",
    },
    {
        "name": "Murasalat Referral Overdue",
        "event": "Days After",
        "days_in_advance": 1,
        "title": "لديك إحالة متأخرة",
        "subject": "الإحالة {{ doc.name }} تجاوزت موعدها {{ doc.due_date }}",
        "message": "إحالة موكولة إليك تجاوزت موعدها. افتحها لإتمامها.",
    },
]

ASSIGNMENT_RULE = {
    "name": "Murasalat Referral Assignment",
    "document_type": REFERRAL,
    "rule": "Based on Field",
    "field": "recipient_user",
    "assign_condition": 'doc.recipient_type == "User" and doc.recipient_user and ({open})'.format(
        open=_OPEN
    ),
    "unassign_condition": _DONE,
    "close_condition": _DONE,
    # The native ToDo then carries the referral's own due date, which is what the ToDo list
    # and calendar sort by.
    "due_date_based_on": "due_date",
    "description": "إحالة {{ doc.name }} تحتاج إجراءً منك. افتحها لاستلامها أو إتمامها.",
    "priority": 1,
    "disabled": 0,
}

# The condition a reminder carries. `frappe` and `doc` are both in the namespace the framework
# evaluates a Notification condition in (`notification.get_context`).
_CONDITION = """doc.due_date \\
and {open} \\
and not frappe.db.exists(
    "Notification Log",
    {{
        "document_type": {doctype},
        "document_name": doc.name,
        "type": {type},
        "title": {title},
    }},
)"""


def reminder_condition(reminder, notification_type):
    """The Python condition for one reminder, keyed on the type it will be logged under."""
    return _CONDITION.format(
        open=_OPEN,
        doctype=repr(REFERRAL),
        type=repr(notification_type),
        title=repr(reminder["title"]),
    )


def _notification_type(name, create=True):
    """Use a dedicated Notification Type when the site can hold one.

    It groups the two reminders apart in the bell, and gives the duplicate guard a stable key.
    A site whose Notification Type doctype refuses the row falls back to the framework's own
    "Alert" type - the two reminders stay distinguishable by their static title, which the
    guard also keys on, so nothing silently misconfigures.

    ``plan`` calls this with ``create=False``: a read-only report must not write a row.
    """
    if frappe.db.exists("Notification Type", name):
        return name

    if not create:
        return "Alert"

    try:
        frappe.get_doc(
            {"doctype": "Notification Type", "notification_type": name}
        ).insert(ignore_permissions=True)
    except Exception:  # noqa: BLE001 - the fallback is a working configuration, not a failure
        return "Alert"

    return name


def _definition(reminder, notification_type):
    return {
        "doctype": "Notification",
        "name": reminder["name"],
        "module": "Murasalat Office",
        "is_standard": 0,
        "enabled": 1,
        "document_type": REFERRAL,
        "event": reminder["event"],
        "date_changed": "due_date",
        "days_in_advance": reminder["days_in_advance"],
        "condition_type": "Python",
        "condition": reminder_condition(reminder, notification_type),
        "channel": "System Notification",
        "notification_type": notification_type,
        "notification_title": reminder["title"],
        "notification_message": reminder["message"],
        "subject": reminder["subject"],
        # No recipient rows on purpose: the assignees are the recipients, and they are resolved
        # from the open ToDo rows at send time.
        "recipients": [],
        "send_to_all_assignees": 1,
        "attach_print": 0,
    }


def _assignment_rule_definition():
    return {"doctype": "Assignment Rule", **ASSIGNMENT_RULE}


def _notification_is_current(name, definition):
    fields = ("condition", "notification_title", "notification_message", "subject",
              "days_in_advance", "event", "channel", "send_to_all_assignees")
    return all(
        _same(frappe.db.get_value("Notification", name, field), definition.get(field))
        for field in fields
    )


def _assignment_rule_is_current(name):
    fields = ("rule", "field", "assign_condition", "unassign_condition", "close_condition",
              "due_date_based_on", "description")
    return all(
        frappe.db.get_value("Assignment Rule", name, field) == ASSIGNMENT_RULE.get(field)
        for field in fields
    )


def _same(left, right):
    """Metadata round-trips a Check as 1 and a Text as a string; compare on the value."""
    return str(left or "") == str(right or "")


def plan():
    """Read-only: what exists, what is out of date, and which Notification Type is in use.

    ``plan`` is what proves the definition reached a site. It also reports the workflow states
    the reminders are keyed on, so a renamed state is visible before a reminder silently stops
    matching.
    """
    rows = []
    for reminder in REMINDERS:
        name = reminder["name"]
        exists = bool(frappe.db.exists("Notification", name))
        rows.append(
            {
                "notification": name,
                "event": reminder["event"],
                "days_in_advance": reminder["days_in_advance"],
                "exists": exists,
                "current": exists and _notification_is_current(
                    name,
                    _definition(
                        reminder, _notification_type(reminder["name"], create=False)
                    ),
                ),
            }
        )

    name = ASSIGNMENT_RULE["name"]
    exists = bool(frappe.db.exists("Assignment Rule", name))
    return {
        "notifications": rows,
        "assignment_rule": {
            "rule": name,
            "field": ASSIGNMENT_RULE["field"],
            "exists": exists,
            "current": exists and _assignment_rule_is_current(name),
        },
        "open_states": list(OPEN_STATES),
    }


def install():
    """Create what is missing and refresh what went stale. Idempotent.

    A reminder whose row differs from the definition is brought up to date: its condition is
    what makes a second scheduler run produce nothing, and a site that installed the definition
    earlier must receive a corrected one. The row is created through Frappe's model either way.
    """
    result = {"notifications": [], "assignment_rule": None, "errors": []}

    for reminder in REMINDERS:
        name = reminder["name"]
        try:
            notification_type = _notification_type(name)
            definition = _definition(reminder, notification_type)

            if not frappe.db.exists("Notification", name):
                frappe.get_doc(definition).insert(ignore_permissions=True)
                result["notifications"].append({"notification": name, "outcome": "created",
                                                "notification_type": notification_type})
                continue

            if _notification_is_current(name, definition):
                result["notifications"].append({"notification": name, "outcome": "exists",
                                                "notification_type": notification_type})
                continue

            # The row is site configuration an administrator may have edited, so only the
            # fields that carry the mechanism are written back.
            frappe.db.set_value(
                "Notification",
                name,
                {key: definition[key] for key in
                 ("condition", "days_in_advance", "event", "date_changed", "channel",
                  "notification_message", "notification_title", "subject",
                  "send_to_all_assignees", "notification_type", "enabled")},
            )
            result["notifications"].append({"notification": name, "outcome": "updated",
                                            "notification_type": notification_type})
        except Exception as exc:  # noqa: BLE001 - one bad row must not stop the other
            result["errors"].append(f"{name}: {exc}")

    name = ASSIGNMENT_RULE["name"]
    try:
        if not frappe.db.exists("Assignment Rule", name):
            frappe.get_doc(_assignment_rule_definition()).insert(ignore_permissions=True)
            result["assignment_rule"] = {"rule": name, "outcome": "created"}
        elif _assignment_rule_is_current(name):
            result["assignment_rule"] = {"rule": name, "outcome": "exists"}
        else:
            frappe.db.set_value(
                "Assignment Rule",
                name,
                {key: ASSIGNMENT_RULE[key] for key in
                 ("rule", "field", "assign_condition", "unassign_condition", "close_condition",
                  "due_date_based_on", "description", "priority")},
            )
            result["assignment_rule"] = {"rule": name, "outcome": "updated"}
    except Exception as exc:  # noqa: BLE001
        result["errors"].append(f"{name}: {exc}")

    return result
