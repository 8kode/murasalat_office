# Operational notifications

Five questions a user has to be able to answer, and the Frappe surface that answers each. The
application ships **no notification engine**: no notification doctype, no custom inbox, no
scheduler, no queue, no transport, no second assignment model.

| The user's question | Native surface | What this app adds |
|---|---|---|
| What arrived? | Assignment -> ToDo + the framework's own assignment notification | An Assignment Rule (configuration) |
| What should I do? | The same ToDo, carrying the referral's due date | `due_date_based_on = due_date` |
| When must I finish? | `Notification`, event **Days Before** | One rule, `days_in_advance = 1` |
| What is late? | `Notification`, event **Days After** | One rule, `days_in_advance = 1` |
| Is a formal action waiting for me? | The framework's **Workflow Action** list | Nothing |

## Why each question lands where it does

**Assignment is the framework's.** `frappe.desk.form.assign_to.add` creates the ToDo, calls
`frappe.share.add` when the assignee cannot already read the record, and writes its own
`Notification Log` of type `Assignment` through `notify_assignment`. So a second "a referral
arrived" notification would be the duplicate the brief forbids. What was missing was not code -
an **Assignment Rule** is what tells Frappe *which* referrals belong to whom:

| Field | Value |
|---|---|
| `rule` | Based on Field |
| `field` | `recipient_user` |
| `assign_condition` | `doc.recipient_type == "User" and doc.recipient_user and (doc.workflow_state in ("Sent", "Received") and not doc.cancelled_on)` |
| `unassign_condition` / `close_condition` | `doc.workflow_state in ("Completed", "Cancelled") or doc.cancelled_on` |
| `due_date_based_on` | `due_date` |

`assignment_rule.apply` is already registered on `doc_events["*"]["on_update"]`, so the rule is
evaluated on every save with no scheduler of ours. And `apply()` calls `apply_assign` **only when
nothing is assigned**, so an unchanged referral cannot announce itself twice - the duplicate guard
for question 1 is the framework's own.

A department-targeted referral assigns to nobody: it names no person, and the brief forbids
notifying a whole department. `Murasalat Inbox` is what tells a department what is waiting.

**The reminders are the framework's date mechanism.** Frappe's daily `trigger_daily_alerts` job
reads every enabled Notification whose event is `Days Before` / `Days After` and matches the named
date field exactly against today. Each rule therefore fires on one day only, and a referral earns
at most two reminders in its life: one the day before its due date, one the day after.

Two native details carry the rest:

* **Recipients are the assignees** - `send_to_all_assignees = 1` resolves the recipients from the
  **open ToDo rows** at send time. Responsibility that ended takes its reminders with it: the
  Assignment Rule's close condition closes the ToDo, `get_assignees` then returns nobody, and
  `create_system_notification` returns early for want of a recipient. A `recipient_user` field
  would keep reminding someone who is no longer responsible; a role recipient would remind every
  holder of the role.
* **The duplicate guard is a condition, not code** - the condition refuses when a
  `Notification Log` of that kind already exists for the document:

  ```python
  doc.due_date \
  and doc.workflow_state in ('Sent', 'Received') and not doc.cancelled_on \
  and not frappe.db.exists(
      "Notification Log",
      {
          "document_type": 'Murasalat Referral',
          "document_name": doc.name,
          "type": 'Murasalat Referral Due Soon',
          "title": 'موعد إحالة يقرب',
      },
  )
  ```

  `notification.get_context` puts `frappe` in the namespace a condition is evaluated in, which is
  what makes this possible without a line of application code. So a second run of the same day's
  job - a re-run, or an administrator calling `trigger_daily_alerts` by hand - writes nothing.

**Nothing was added for workflow actions.** Frappe already keeps a `Workflow Action` row per
pending transition and shows it to the roles allowed to act. Turning on the Workflow's
`send_email_alert` would additionally email **every** holder of the role, which is exactly the
"do not notify everyone" case the brief rules out. An administrator who wants that email can tick
the box in Desk; the app does not decide it.

## The messages

Short, Arabic, and carrying the referral's own identity only:

| Rule | Bell headline (`notification_title`) | Detail (`subject`, rendered) |
|---|---|---|
| Due soon | `موعد إحالة يقرب` | `الإحالة {{ doc.name }} موعدها {{ doc.due_date }}` |
| Overdue | `لديك إحالة متأخرة` | `الإحالة {{ doc.name }} تجاوزت موعدها {{ doc.due_date }}` |

The headline is deliberately **static**: it is both the bell's category and part of the duplicate
guard's key, so it must not depend on the document's values. The referral number and the date go
in the subject, which the bell shows next to it.

The body names the referral and its date and **nothing from the parent correspondence** - no
subject, no sender, no body text. That is deliberate: nothing checks that a recipient can read the
record before a Notification Log is written for them (the framework scopes the log to its
`for_user`, not to the document), so the payload is what keeps a stale assignee from reading the
parent file. The notification's link opens the referral, where the normal permission check applies.

The framework's own assignment notice (`{0} assigned a new task {1} {2} to you`) is Frappe's
string; the app translates it through `translations/ar.csv`, which is how a native message becomes
Arabic without a line of code. The same file translates the ToDo description, the
"already in the list" and the "shared with" messages.

## Applying it

```bash
bench --site <site> execute murasalat_office.setup.notifications.plan     # read-only
bench --site <site> execute murasalat_office.setup.notifications.install
```

`provision.apply` already calls `install()` and `provision.readiness` reports each row as
`PASS` / `FAIL`, so a normal launch does both in one command. `plan()` reports, per reminder and
for the rule, whether the row exists and whether it is current - and it never writes: a report a
person runs to check a site must not configure it.

A row that differs from the definition is brought up to date, because the condition *is* the
duplicate guard. A row an administrator has restyled by hand keeps its own wording unless the
mechanism fields differ.

## Nothing else fires

Everything the brief lists as unwanted stays unwanted without a rule to suppress it: topic edits,
ordinary field edits, opening a record, saving a record, and notes produce no notification,
because a notification exists only where one of the five questions has an answer. There is no
`New` or `Save` event rule in this app - the framework announces an assignment by itself, and the
two reminders cover the dates.

## Verification

```bash
python -m pytest murasalat_office/tests/test_notifications.py -q
```

The suite executes both Notification conditions and all three Assignment Rule conditions against
documents built to match the ten cases - open, undated, drafted, completed, cancelled, late,
already reminded - and holds the mechanism to what the framework demands: a date field for
`Days Before` / `Days After`, no `frappe` in an Assignment Rule condition (its namespace is the
document alone), valid Python in every condition (a broken one throws on a scheduler run), and a
`plan()` that writes nothing. It also fails if the branch grows a scheduler, a notification
doctype, or a `Notification Log` insert.

What it cannot prove, and what a site must: that the bell shows the message and that a reminder
reaches the assignee. `provision.readiness` proves the rows exist and are current;
`bench --site <site> execute frappe.email.doctype.notification.notification.trigger_daily_alerts`
runs the framework's own job on demand to see one.

## Residual risks

* **A stale assignee.** If a user keeps an open ToDo for a referral they can no longer read, the
  reminder still reaches them - the payload is limited to the referral's identity, and its link
  fails the permission check on open. Closing the ToDo ends it.
* **A due date set in the past.** The framework matches the date field exactly, so a referral
  created already overdue misses its single "overdue" day. It still shows as overdue in the list
  indicator, in `Murasalat Overdue Referrals`, and on the form.
* **Notification Settings.** A user who disabled notifications (`is_notifications_enabled`) is
  filtered out by the framework before a log is written. That is the user's own choice, and the
  app does not override it.
