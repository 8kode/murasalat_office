# Launch setup

What a fresh site needs before the first user can create a correspondence record, in the
order it has to happen. Everything here is run by the site administrator; nothing in this
application applies itself on install or on migrate.

---

## 1. Install and migrate

```bash
cd ~/frappe-bench
bench get-app /path/to/murasalat_office
bench --site <site> install-app murasalat_office
bench --site <site> migrate
```

## 2. Seed the master data (required)

Without this step the **first save fails**. `Murasalat Correspondence` carries four
required Link fields whose field defaults point at records that do not exist yet:

| Field | Links to | Default value |
|---|---|---|
| `transaction_type` | Murasalat Transaction Type | `مذكرة` |
| `confidentiality` | Murasalat Confidentiality Level | `عام` |
| `importance` | Murasalat Importance Level | `متوسط` |
| `correspondence_direction` | Murasalat Correspondence Direction | `Internal` |

```bash
bench --site <site> execute murasalat_office.setup.master_data.seed
```

The call returns three lists — `created`, `exists`, `planned` — plus
`missing_required`, which is empty once the launch-critical values are in place. It is
safe to re-run: a record is created only when it is missing. Use
`--kwargs "{'dry_run': True}"` to see the plan without writing anything.

`Murasalat Correspondence Direction` must keep the three names `Incoming`, `Outgoing`
and `Internal`: `services.lifecycle.register_correspondence` resolves the initial holder
from a dictionary keyed on exactly those strings. Renaming one breaks registration.

The seeded titles are a reviewable starting set, not a business decision — rename or
extend them in Desk at any time.

## 3. Permissions (required)

A DocType that ships no DocPerm row is reachable only by `Administrator`. Read the plan,
then either materialise it or follow it by hand:

```bash
bench --site <site> execute murasalat_office.setup.governance_plan.describe
bench --site <site> execute murasalat_office.setup.governance_plan.materialize \
    --kwargs "{'confirm': True}"
```

`describe` only prints. `materialize` creates the three roles and their native DocPerm
rows, is idempotent, and refuses to run without `confirm=True`. It never creates a
workflow. Role names it can create: `Correspondence Clerk`, `Correspondence Supervisor`,
`Correspondence Auditor` — the auditor is read-only by design, because an auditor must
not be able to alter a sealed record.

Deletion rights are deliberately withheld from all three: deleting a correspondence
record destroys the sealed audit trail this application exists to preserve.

## 4. Workflows (required for the lifecycle)

The application's seven lifecycle methods do not run on their own. Follow
[`WORKFLOW_GOVERNANCE.md`](WORKFLOW_GOVERNANCE.md) — it carries the exact task names, the
Desk steps, and the asynchronous trap that silently turns all seven into no-ops.

The plan is in `governance_plan.describe()`; the shape is:

| Workflow | Transitions | Task attached |
|---|---|---|
| Murasalat Correspondence Lifecycle | Draft → Registered | `Register Correspondence` |
| | Registered → Closed | `Close Correspondence` |
| | Closed → Sealed | `Seal Correspondence` |
| | Sealed → Registered | `Reopen Correspondence` |
| Murasalat Referral Lifecycle | Draft → Sent | `Send Referral` |
| | Sent → Received | `Receive Referral` |
| | Received → Completed | `Complete Referral` |

Then verify with:

```bash
bench --site <site> execute murasalat_office.services.governance.workflow_task_readiness
```

## 5. Assignment and notifications

Not shipped: assignment is native Frappe. Create an **Assignment Rule** on
`Murasalat Referral` (Desk → Assignment Rule) so a routed referral lands in the
recipient's To-Do list. The referral is the work item; the To-Do identifies the user. This
is why the application hooks no `doc_events` for ToDo.

## 6. Before showing it to anyone

- Create at least one `Department` and one internal `User`, then a
  `Murasalat User Organization Membership` for each — the Inbox scopes resolve
  organization from membership rows.
- Walk the acceptance path on a non-Administrator account: create a correspondence →
  Register → create a referral → Send → Receive → Complete → Close → Seal →
  try to edit the sealed record (must be refused) → print.
- Print at least one correspondence and one referral notification: two standard print
  formats ship with the application — see [PRINT_FORMATS.md](PRINT_FORMATS.md).

## Verification summary

| Check | Command | Expected |
|---|---|---|
| Master data present | `master_data.seed` → `missing_required` | `[]` |
| Permissions present | `governance_plan.describe` then Role Permission Manager | a row per role and DocType |
| Lifecycle wired | `governance.workflow_task_readiness` | no FAIL, no asynchronous WARN |
| Print formats available | Print menu on a record | both formats listed and print in Arabic |
| Regression suite | `python -m pytest murasalat_office/tests -q` | green |
