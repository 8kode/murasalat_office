"""Operational notifications, assembled from Frappe's own building blocks.

What each question a user has gets, and the native surface that answers it:

1. *what arrived* and 2. *what should I do*
       Native **Assignment**: an Assignment Rule assigns a sent, user-targeted referral to
       ``recipient_user``. That creates the framework's own ToDo, its own share when the
       assignee cannot already read the record, and its own Notification Log of type
       "Assignment" - so no second notification is written for the same event.
3. *when must I finish* and 4. *what is late*
       Native **Notification** rows on the framework's Days Before / Days After mechanism,
       driven by the daily ``trigger_daily_alerts`` job and delivered to the in-app bell.
5. *is a formal action waiting for me*
       Nothing added. Frappe's own Workflow Action list shows the transitions a user's role
       may act on - and ``provision`` now creates the Approval Workflow, so an approval
       waiting for a supervisor appears in that list like any other pending transition.

Plus one notice that closes the loop in the other direction: whoever sent a referral is told
when it is received and when it is completed, through a native **Value Change** rule on
``workflow_state`` whose recipient is the document's own ``owner`` field.

There is no notification doctype, no inbox, no queue, no scheduler and no transport in this
module. It creates native rows through Frappe's own models, exactly as clicking through Desk
would - the pattern ``provision.py`` and ``report_print_formats.py`` already use.

Four decisions worth the sentence:

* **Reminder recipients are the assignees, not ``recipient_user``.** A completed referral must
  stop reminding anyone. ``send_to_all_assignees`` resolves the recipients from the Open ToDo
  rows, so responsibility that ended takes its reminders with it - the Assignment Rule's close
  condition is what ends it. ``recipient_user`` would keep reminding a user who is no longer
  responsible, and a role recipient would remind every holder of the role.
* **The day before, the day itself, and the day after.** The framework matches the date field
  exactly, so each reminder fires on one day only - and a referral earns at most three reminders
  in its life, one per day. ``days_in_advance`` is an Int field: changing a lead time is a Desk
  edit, not a release. The middle one is not decoration: with only the outer two, the day a
  referral is actually due was the one day nothing reached the person who owes it.
* **The duplicate guard is a condition, not code.** The date match already limits a reminder to
  one day; the condition additionally refuses when a Notification Log of that kind - matched on
  the rule's own type *and* its title - already exists for the document, so a second run of the
  same day's job writes nothing. Both keys are stored so that neither a translated title nor a
  missing Notification Type can open the door.
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

# The condition a reminder must satisfy. Spelled once and reused, so the three reminders cannot
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
        "name": "Murasalat Referral Due Today",
        "event": "Days Before",
        "days_in_advance": 0,
        "title": "إحالة تستحق اليوم",
        "subject": "الإحالة {{ doc.name }} موعدها اليوم",
        "message": "إحالة موكولة إليك موعدها اليوم. افتحها لتسجيل ما تم.",
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

# The loop in the other direction: whoever created the referral is the clerk who sent it, so the
# document's own `owner` field names the person to tell. Value Change fires only when the state
# actually changes, so each of these is written at most once per referral - no guard needed, and
# no notice for the person who performed the action (the framework skips a self-notification).
SENDER_NOTICES = [
    {
        "name": "Murasalat Referral Received",
        "state": "Received",
        "title": "تم استلام إحالتك",
        "subject": "استُلمت الإحالة {{ doc.name }}",
        "message": "أكّد المستلم استلام الإحالة. تابعها لمعرفة ما تم.",
    },
    {
        "name": "Murasalat Referral Completed",
        "state": "Completed",
        "title": "تم إتمام إحالتك",
        "subject": "أُتمَّت الإحالة {{ doc.name }}",
        "message": "أُتمَّت الإحالة. راجع نتيجتها في سجل الإحالة.",
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

REMINDER_FIELDS = ("condition", "notification_title", "notification_message", "subject",
                   "days_in_advance", "event", "date_changed", "channel",
                   "send_to_all_assignees", "notification_type")
NOTICE_FIELDS = ("condition", "notification_title", "notification_message", "subject",
                 "event", "value_changed", "channel", "send_to_all_assignees",
                 "notification_type")


def reminder_condition(reminder, notification_type):
    """The Python condition for one reminder, keyed on the type it will be logged under."""
    return _CONDITION.format(
        open=_OPEN,
        doctype=repr(REFERRAL),
        type=repr(notification_type),
        title=repr(reminder["title"]),
    )


def notice_condition(notice):
    """The condition for a sender notice: the one state it exists to announce."""
    return 'doc.workflow_state == {state}'.format(state=repr(notice["state"]))


# The framework requires a row per day in `assignment_days` and refuses a rule without one. The
# child's fieldname AND its allowed values are read from the live meta - `day` is a Select, and
# Frappe validates the value against its options.
DEFAULT_WEEKDAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")


def _assignment_rule_document():
    """The Assignment Rule as a document Frappe will accept.

    Assigning a referral to its recipient is the mechanism that tells the framework who owes an
    action, so the rule has to exist. It did not, silently: ``assignment_days`` is required and was
    missing, the insert threw, and the message went into ``install()``'s own report, which nothing
    printed. ``setup/install.py`` now surfaces those.
    """
    definition = {"doctype": "Assignment Rule", **ASSIGNMENT_RULE}
    if definition.get("assignment_days"):
        return definition

    field = frappe.get_meta("Assignment Rule").get_field("assignment_days")
    if not field:
        return definition

    if field.fieldtype in ("Table", "Table MultiSelect"):
        child = frappe.get_meta(field.options)
        day_field = _field(child, "day", "day_of_week")
        options = (child.get_field(day_field).options or "").splitlines()
        weekdays = [option.strip() for option in options if option.strip()] or list(DEFAULT_WEEKDAYS)
        definition["assignment_days"] = [{day_field: day} for day in weekdays]
    else:
        definition["assignment_days"] = len(DEFAULT_WEEKDAYS)

    return definition


def _field(meta, *candidates):
    """The first of these fieldnames the live meta declares."""
    for candidate in candidates:
        if meta.get_field(candidate):
            return candidate
    frappe.throw(
        _("None of {0} exists on {1}.").format(", ".join(candidates), meta.name)
    )


def _notification_type(name, create=True):
    """Use a dedicated Notification Type when the site can hold one.

    It groups the reminders apart in the bell, and gives the duplicate guard a stable key.
    A site whose Notification Type doctype refuses the row falls back to the framework's own
    "Alert" type - the reminders stay distinguishable by their static title, which the guard
    keys on as well, so nothing silently misconfigures.

    ``plan`` calls this with ``create=False``: a read-only report must not write a row.
    """
    if frappe.db.exists("Notification Type", name):
        return name

    if not create:
        return "Alert"

    try:
        # The doctype's autoname is `field:type_name`, and its data field is `type_name` - not
        # `notification_type`, which is the *Notification's* own field. Naming it wrong here
        # throws inside the insert and this silently downgrades to "Alert".
        frappe.get_doc({"doctype": "Notification Type", "type_name": name}).insert(
            ignore_permissions=True
        )
    except Exception:  # noqa: BLE001 - the fallback is a working configuration, not a failure
        return "Alert"

    return name


def _definition(spec, notification_type):
    """One Notification row, for either kind: a dated reminder, or a state notice."""
    if "days_in_advance" in spec:
        return {
            "doctype": "Notification",
            "name": spec["name"],
            "module": "Murasalat Office",
            "is_standard": 0,
            "enabled": 1,
            "document_type": REFERRAL,
            "event": spec["event"],
            "date_changed": "due_date",
            "days_in_advance": spec["days_in_advance"],
            "condition_type": "Python",
            "condition": reminder_condition(spec, notification_type),
            "channel": "System Notification",
            "notification_type": notification_type,
            "notification_title": spec["title"],
            "notification_message": spec["message"],
            "subject": spec["subject"],
            # No recipient rows on purpose: the assignees are the recipients, and they are
            # resolved from the open ToDo rows at send time.
            "recipients": [],
            "send_to_all_assignees": 1,
            "attach_print": 0,
        }

    return {
        "doctype": "Notification",
        "name": spec["name"],
        "module": "Murasalat Office",
        "is_standard": 0,
        "enabled": 1,
        "document_type": REFERRAL,
        "event": "Value Change",
        "value_changed": "workflow_state",
        "condition_type": "Python",
        "condition": notice_condition(spec),
        "channel": "System Notification",
        "notification_type": notification_type,
        "notification_title": spec["title"],
        "notification_message": spec["message"],
        "subject": spec["subject"],
        # The document's own owner field is the framework's supported way to name a recipient
        # from the record (`Notification.get_list_of_recipients` resolves it to a User).
        "recipients": [{"receiver_by_document_field": "owner"}],
        "send_to_all_assignees": 0,
        "attach_print": 0,
    }


def _all_specs():
    for spec in REMINDERS:
        yield spec, REMINDER_FIELDS, "reminder"
    for spec in SENDER_NOTICES:
        yield spec, NOTICE_FIELDS, "notice"


def _notification_is_current(name, definition, fields):
    return all(
        _same(frappe.db.get_value("Notification", name, field), definition.get(field))
        for field in fields
    )


def _assignment_rule_is_current(name):
    fields = ("rule", "field", "assign_condition", "unassign_condition", "close_condition",
              "due_date_based_on", "description")
    if not all(
        frappe.db.get_value("Assignment Rule", name, field) == ASSIGNMENT_RULE.get(field)
        for field in fields
    ):
        return False

    # A rule with no assignment_days row is not a working rule, whatever its other fields say.
    return bool(frappe.get_doc("Assignment Rule", name).get("assignment_days"))


def _same(left, right):
    """Metadata round-trips a Check as 1 and a Text as a string; compare on the value."""
    return str(left or "") == str(right or "")


def plan():
    """Read-only: what exists, what is out of date, and which Notification Type is in use.

    ``plan`` is what proves the definition reached a site. It also reports the workflow states
    the reminders are keyed on, so a renamed state is visible before a reminder silently stops
    matching. It writes nothing: a report a person runs to check a site must not configure it.
    """
    rows = []
    for spec, fields, kind in _all_specs():
        name = spec["name"]
        exists = bool(frappe.db.exists("Notification", name))
        rows.append(
            {
                "notification": name,
                "kind": kind,
                "event": spec.get("event") or "Value Change",
                "days_in_advance": spec.get("days_in_advance"),
                "exists": exists,
                "current": exists and _notification_is_current(
                    name,
                    _definition(spec, _notification_type(name, create=False)),
                    fields,
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

    A row whose mechanism fields differ from the definition is brought up to date: a reminder's
    condition is what makes a second scheduler run produce nothing, and a site that installed the
    definition earlier must receive a corrected one. The row is created through Frappe's model
    either way.
    """
    result = {"notifications": [], "assignment_rule": None, "errors": []}

    for spec, fields, kind in _all_specs():
        name = spec["name"]
        try:
            notification_type = _notification_type(name)
            definition = _definition(spec, notification_type)

            if not frappe.db.exists("Notification", name):
                frappe.get_doc(definition).insert(ignore_permissions=True)
                result["notifications"].append({"notification": name, "kind": kind,
                                                "outcome": "created",
                                                "notification_type": notification_type})
                continue

            if _notification_is_current(name, definition, fields):
                result["notifications"].append({"notification": name, "kind": kind,
                                                "outcome": "exists",
                                                "notification_type": notification_type})
                continue

            # The row is site configuration an administrator may have edited, so only the fields
            # that carry the mechanism are written back.
            frappe.db.set_value(
                "Notification", name,
                {key: definition[key] for key in fields if key in definition},
            )
            result["notifications"].append({"notification": name, "kind": kind,
                                            "outcome": "updated",
                                            "notification_type": notification_type})
        except Exception as exc:  # noqa: BLE001 - one bad row must not stop the others
            result["errors"].append(f"{name}: {exc}")

    name = ASSIGNMENT_RULE["name"]
    try:
        if not frappe.db.exists("Assignment Rule", name):
            frappe.get_doc(_assignment_rule_document()).insert(ignore_permissions=True)
            result["assignment_rule"] = {"rule": name, "outcome": "created"}
        elif _assignment_rule_is_current(name):
            result["assignment_rule"] = {"rule": name, "outcome": "exists"}
        else:
            frappe.db.set_value(
                "Assignment Rule", name,
                {key: ASSIGNMENT_RULE[key] for key in
                 ("rule", "field", "assign_condition", "unassign_condition", "close_condition",
                  "due_date_based_on", "description", "priority")},
            )
            result["assignment_rule"] = {"rule": name, "outcome": "updated"}
    except Exception as exc:  # noqa: BLE001
        result["errors"].append(f"{name}: {exc}")

    return result
