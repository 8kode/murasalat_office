# Workflow transition tasks

How a Desk Workflow calls this application's lifecycle methods — and what silently stops
working when it does not.

**Audience:** whoever configures the site (Desk administrator or implementation partner).
**Scope:** configuration only. This application ships no Workflow, no Workflow State, no
role, and no permission rows. Every setting described here lives in Desk and stays there.

Structures in this document were read from the framework source on 2026‑09‑23
(`frappe/model/workflow.py`, and the `Workflow Transition`, `Workflow Transition Tasks`
and `Workflow Transition Task` DocTypes on the `develop` branch).

---

## 1. The failure this document prevents

`murasalat_office/hooks.py` declares a `workflow_methods` hook with seven lifecycle
methods. **Declaring them does not run them.**

Frappe dispatches those methods only when a Workflow transition carries a *Workflow
Transition Task* row whose `Task` matches the hook `name` exactly. The dispatch happens
inside `apply_workflow` in `frappe/model/workflow.py`:

```python
tasks = {i["name"]: i["method"] for i in frappe.get_hooks("workflow_methods")}
...
try:
    task_method = frappe.get_attr(tasks[workflow_transition.task])
except KeyError:
    frappe.throw(_('There is no task called "{}"').format(workflow_transition.task))
```

Two failure modes follow directly from that code:

| Situation | What happens |
|---|---|
| No transition task attached to a transition | The method never runs. The transition still completes. Nothing is written, and no error is raised. |
| A transition task names something the hook does not declare (a typo, or a name changed in code) | **Every** transition using that task throws `There is no task called "…"`. The workflow becomes unusable until the row is fixed. |

The first row is the dangerous one. Consider a Workflow whose *Close* transition has no
task attached: the Correspondence is closed without `close_correspondence` running, so
`closed_on` stays empty and — more seriously — the rule that refuses to close a file while
it still has open referrals is bypassed entirely. Nothing in the UI reports a problem.

---

## 2. How the pieces fit together in Desk

```
Workflow
└── Workflow Transition  (child table: state → action → next_state → allowed role)
    └── Transition Tasks  (Link → a "Workflow Transition Tasks" document)
        └── Workflow Transition Tasks  (standalone document, named by the administrator)
            └── Tasks  (child table: Workflow Transition Task rows)
                ├── Task           Select — the hook name from workflow_methods
                ├── Enabled        Check — default on
                ├── Asynchronous   Check — must stay OFF (see §5)
                └── Link           Dynamic Link — only for "Server Script" / "Webhook"
```

Notes confirmed against the framework definitions:

- `Workflow Transition Tasks` is a standalone DocType with naming rule *Set by user*
  (`autoname: prompt`) and a single field, `tasks`, pointing at the child table. Its own
  permissions are granted to **System Manager** only — so a System Manager must create it.
- `Workflow Transition Task` is a child table. Its `Task` field is a Select with **no
  static option list** in the DocType definition: the available names come from the
  installed applications' `workflow_methods` hooks. If the picker appears empty, the hook
  is not being read (wrong app branch, or an un-migrated site) — do not type a name by
  hand into a Select field.
- `Link` is mandatory only when `Task` is `Server Script` or `Webhook`. For the seven
  application tasks below it stays empty.
- The official framework walkthrough is
  <https://docs.frappe.io/erpnext/user/manual/en/workflow-transition-tasks>.

---

## 3. The seven application tasks

Each name below must match `hooks.py` **character for character**, including capitalisation
and spacing. The `Method` column is resolved from the hook at runtime.

| # | Task name (exact) | Method | Target DocType |
|---|---|---|---|
| 1 | `Register Correspondence` | `services.lifecycle.register_correspondence` | Murasalat Correspondence |
| 2 | `Close Correspondence` | `services.lifecycle.close_correspondence` | Murasalat Correspondence |
| 3 | `Seal Correspondence` | `services.lifecycle.seal_correspondence` | Murasalat Correspondence |
| 4 | `Reopen Correspondence` | `services.lifecycle.reopen_correspondence` | Murasalat Correspondence |
| 5 | `Send Referral` | `services.lifecycle.send_referral` | Murasalat Referral |
| 6 | `Receive Referral` | `services.lifecycle.receive_referral` | Murasalat Referral |
| 7 | `Complete Referral` | `services.lifecycle.complete_referral` | Murasalat Referral |

### What each one writes, and what breaks without it

| Task | Writes on success | Records activity | If never dispatched |
|---|---|---|---|
| `Register Correspondence` | `registered_on`, `current_holder` (resolved from the direction: incoming target, outgoing source, or internal target) | `Registered` | The letter is never registered; no holder is established; `registered_on` stays empty. Throws if the direction is not one of Incoming/Outgoing/Internal, or if the resolved holder is empty. |
| `Close Correspondence` | `closed_on` | `Closed` | `closed_on` stays empty. **The open-referral guard is skipped**, so a file with live referrals can be closed. |
| `Seal Correspondence` | `record_sealed_on`, `record_sealed_by` | `Sealed` | No seal, and therefore no integrity hash: the record stays editable forever and cannot be verified for audit. |
| `Reopen Correspondence` | `reopened_on`, `reopened_by`, clears `closed_on` | `Reopened` | Reopening appears to work in the UI but writes nothing; the record stays logically closed. |
| `Send Referral` | `sent_on` on the Referral, plus a `Referral Sent` row on the **parent Correspondence** | `Referral Sent` | `sent_on` stays empty, so the referral never enters an open-referral filter and every overdue/due-today report overlooks it. |
| `Receive Referral` | `received_on`, `received_by`; for Department-targeted referrals also moves the parent `current_holder` | `Referral Received` | Receipt is invisible to the reports; the organisational holder never changes. A later completion throws because the referral was never received. |
| `Complete Referral` | `completed_on`, `completed_by` | `Referral Completed` | Work never closes: it stays in every open queue and blocks the parent from closing. |

Every method opens with a DocType guard (`if doc.doctype != …: frappe.throw(…)`), so
attaching a task to the wrong Workflow fails loudly instead of writing nonsense. Keep any
future Workflow scoped to the DocType named above.

---

## 4. Configuring it in Desk

Do this once per site, after `bench migrate` and after the application's Workflows exist.

1. **Create the task group.** New → *Workflow Transition Tasks*. Give it a name that says
   what it is, for example `Murasalat Correspondence Lifecycle`. (This DocType is named by
   you, not by a series.)
2. **Add one row per lifecycle step you intend to use.** In the `Tasks` table, set
   `Task` to an exact name from §3, leave `Enabled` ticked, and leave `Asynchronous`
   **unticked**. `Link` stays empty.
3. **Attach the group to each transition.** Open the Workflow (Settings → Workflow), then
   for every transition that should move state, set `Transition Tasks` to the document you
   created in step 1. A transition with an empty `Transition Tasks` runs no application
   code at all.
4. **Verify in the product, not on this page.** Run through §6.

You do not need one task group per transition — several transitions may share one
document. What matters is that every transition that changes lifecycle state points at a
group containing the right task.

### Which transitions must carry a task

| Workflow | Transition action (name it as you like) | Task that must be attached |
|---|---|---|
| Murasalat Correspondence | Register / Regist | `Register Correspondence` |
| Murasalat Correspondence | Close / Archive | `Close Correspondence` |
| Murasalat Correspondence | Seal / Lock | `Seal Correspondence` |
| Murasalat Correspondence | Reopen / Reconsider | `Reopen Correspondence` |
| Murasalat Referral | Send / Route | `Send Referral` |
| Murasalat Referral | Receive / Acknowledge | `Receive Referral` |
| Murasalat Referral | Complete / Finish | `Complete Referral` |

If a transition only moves between working states (for example *Draft* → *Review*) it needs
no task. The rule is: attach a task whenever the transition is supposed to write one of the
fields listed in §3.

---

## 5. Hard rules

**Keep `Asynchronous` unticked.** These methods mutate the document in memory and rely on
the save performed by `apply_workflow` at the end of the same transaction, so that
validation failures roll the transition back. Frappe branches on this flag: a synchronous
task runs as `sync_task(doc)` inside the transaction, while an asynchronous one runs as
`frappe.enqueue(async_task, doc=doc, enqueue_after_commit=True)`. Because our methods never
call `save()` themselves, an asynchronous task mutates a detached copy in a background job
and persists nothing — and any `frappe.throw` inside it fires *after* the transition has
already committed. Ticking the box turns all seven methods into silent no-ops.

**Never rename a hook name on one side only.** Changing the `name` in `hooks.py` without
renaming the Desk row (or the reverse) makes every affected transition throw. Rename in
both places in the same change.

**Never bypass a task to "unblock" a user.** `close_correspondence` refusing to close a
file with open referrals is the invariant doing its job. Detach the task to make the error
go away and the same close will succeed without writing `closed_on` — the worst of both
outcomes.

**Do not create these documents as fixtures.** Governance stays in Desk on purpose; see §8.

---

## 6. Verification

Application side — the read-only readiness diagnostic reports, for each active Workflow on
a governed DocType, which transitions carry tasks and whether those tasks are safe:

```bash
bench --site <site> execute murasalat_office.services.governance.workflow_task_readiness
```

It flags:

- a transition task name the hook does not declare (fatal, throws at runtime),
- a task row with `Asynchronous` enabled (silent no-op),
- a disabled task row,
- transitions with no `Transition Tasks` attached.

The same checks appear in the **Murasalat Security Health** report and through the
`get_governance_health` API (System Manager only). The diagnostic only reads — it never
creates or edits a Workflow, a task group, or a hook.

Functional side — do this on a staging site with a non-Administrator user:

1. Create a Correspondence, then apply the *Register* action. Confirm `registered_on` and
   `current_holder` are filled and a `Registered` row appears in Activity History.
2. Create a Referral against it and apply *Send*, then *Receive*, then *Complete*. Confirm
   `sent_on` / `received_on` / `completed_on` and the three activity rows on the parent.
3. Try to *Close* the Correspondence while a referral is still open. It must be refused
   with "The correspondence cannot be closed while it has open referrals."
4. Apply *Close*, then *Seal*. Confirm `record_sealed_on`, `record_sealed_by`, and that
   `integrity_hash` is populated.
5. Edit a sealed record and save. It must be refused.
6. Apply *Reopen*. Confirm `reopened_on` is set, `closed_on` cleared, and a `Reopened` row
   recorded.

Any step that passes silently without its field being written means the transition is
missing its task.

---

## 7. Permission prerequisites

Native Frappe permissions still govern everything; the tasks do not grant access.

- The acting user needs **read** on the parent Correspondence to send, receive, or
  complete a referral (`_get_referral_correspondence` calls `check_permission("read")`).
- Sending a referral also writes an activity row onto the parent and saves it, so the actor
  needs **write** on the Correspondence. The same applies to receiving a
  Department-targeted referral, which moves `current_holder`.
- Grant these through **Role Permission Manager** — the same place every other right on
  these DocTypes is granted.

---

## 8. What this application deliberately does not ship

No Workflow definitions, Workflow States, Workflow Actions, Workflow Transition Tasks,
roles, or permission rows are packaged. There is no `fixtures` hook. This is the
Native‑First principle stated in the README: the site's governance is the site
administrator's configuration, and the application only provides the lifecycle methods the
configuration can call.

The one thing the code base does own is the **contract**: the seven names in
`hooks.py`, the methods behind them in `services/lifecycle.py`, and a regression test
(`tests/test_workflow_task_contract.py`) that fails if a hook name, its method, its DocType
guard, or its entry in this document drifts apart.
