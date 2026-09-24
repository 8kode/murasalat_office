# Audit and Cleanup — whole-surface review

Branch `chore/audit-and-cleanup`, on top of `4d5b701`. Brief: review every form and
every line of code, fix any error, and remove what is unused.

## 1. Method

Static and executable checks only. This sandbox has no bench, no site and no Frappe,
so nothing below is a UI verification.

| Check | How | Result |
|---|---|---|
| Python syntax and imports | `python3 -m compileall murasalat_office` | OK |
| Contract and unit tests | `python3 -m pytest murasalat_office/tests -q` | 451 passed, 3 skipped |
| DocType / Report metadata | `python3 murasalat_office/tests/validate_metadata.py` | passed |
| Report print layout | `node murasalat_office/tests/render_report_template.mjs` (Frappe's real microtemplate engine) | passed |
| Translation coverage | AST extraction of every `_()` / `__()` literal in `.py`, plus `.js` / `.html` scanning, matched against `ar.csv` | 184 live strings, 0 regressions from this branch |
| Sidebar / Workspace links | every `link_to` resolved against shipped DocTypes, Reports and Workspaces | all resolve |
| Orphan schema fields | JSON self-reference: `title_field`, `search_fields`, `fetch_from`, `depends_on`, `in_list_view`, Select options, code search | 5 examined, 0 removed (reasons in §3) |

## 2. Fixed in this branch

### 2.1 Three dead imports removed

| File | Removed |
|---|---|
| `murasalat_office/murasalat_office/doctype/murasalat_correspondence/murasalat_correspondence.py` | `from frappe.utils import now_datetime` |
| `murasalat_office/murasalat_office/report/murasalat_management_summary/murasalat_management_summary.py` | `REFERRAL` (from `services.management`) |
| `murasalat_office/tests/test_verification_contracts.py` | `import json` |

Each was proven dead by a whole-package search for the symbol: the only hit was the
import line itself.

### 2.2 Retired Arabic vocabulary deleted (64 rows; `ar.csv` 457 -> 393)

`ar.csv` still carried translations for labels and messages that exist nowhere in the
app any more. Method: extract every string literal from `.py`, `.js`, `.json`,
`.html`, `.md`; normalise whitespace and join literals split across lines; keep a row
only if its English source appears in that corpus, or in Frappe's own Arabic catalogue
(`frappe/locale/ar.po`, 6283 msgids), or in live model vocabulary (fieldnames, Select
options, DocType names, seeded master-data names).

Deleted — dead app vocabulary with no code, metadata or framework string behind it:

* `Murasalat Correspondence Type`
* `Correspondence Type`
* `General Due Date`
* `Security / Audit`
* `Operational Activity`
* `Current Holder User`
* `Originating Organization`
* `Record Sealed On`
* `Record Sealed By`
* `Incoming Parties`
* `Incoming From`
* `Target Entry`
* `Outgoing Parties`
* `Target Entity`
* `Internal Parties`
* `To Organization`
* `Reference To`
* `Pending Receipt`
* `Very Urgent`
* `Memo`
* `Circular`
* `MY WORK`
* `OPERATIONS`
* `Approval Requests`
* `Delegations`
* `Visible Referrals`
* `Active Items`
* `Navigate`
* `A referral must be linked to a Correspondence before it can be sent.`
* `Recipient Type is required before sending the referral.`
* `Recipient Department is required before sending the referral.`
* `Recipient User is required before sending the referral.`
* `Recipient Type must be User or Organization.`
* `User referrals require a user recipient and no organization recipient.`
* `Organization referrals require an organization recipient and no user recipient.`
* `Unknown inbox scope: {scope}`
* `Registration Number`
* `Registration Date`
* `Document Category`
* `Is Secret`
* `Organization Scope`
* `Governance Health`
* `Follow Up Required`
* `Follow Up Date`
* `Source Entity`
* `External — From / To`
* `Internal user sending the correspondence.`
* `Internal user receiving the correspondence.`
* `External party sending the correspondence.`
* `External party that received the correspondence.`
* `Receiving User`
* `Sending User`
* `Content & Notes`
* `Related Referrals`
* `Correspondence Details`
* `Referral Details`
* `Related Correspondence`
* `Security & Audit`
* `Correspondence Summary`
* `Referral Summary`
* `Murasalat Summary`
* `ATTENTION`
* `Attachments Gallery`
* `Recipient Type must be User or Department.`

Kept deliberately — 274 rows the app itself does not reference:

* `source`
* `Murasalat Correspondence`
* `Murasalat Referral`
* `Murasalat Approval Request`
* `Murasalat Delegation`
* `Murasalat Attachment`
* `Murasalat Correspondence Link`
* `Murasalat Correspondence Activity`
* `Murasalat Confidentiality Level`
* `Murasalat Importance Level`
* `Murasalat Transaction Type`
* `Murasalat Referral Direction`
* `Murasalat External Party`
* `Murasalat External Party Type`
* `Murasalat User Organization Membership`
* `Murasalat Inbox`
* `Murasalat My Work`
* `Murasalat Due Today`
* `Murasalat Follow Up Queue`
* `Murasalat Overdue Referrals`
* `Murasalat Work Queue`
* `Murasalat Employee Productivity`
* `Murasalat Security Health`
* `Murasalat Overdue`
* `Native Frappe correspondence record. Permissions and lifecycle governance are administered from Desk.`
* `Standalone referral with native Frappe permissions and Desk-managed Workflow.`
* `Approval request governed by native Frappe Workflow and permissions configured from Desk.`
* `Classification`
* `Dates`
* `External Letter Number`
* `External Letter Date`
* `Page Count`
* `Concerned Person`
* `Identity`
* `Content`
* `Notes`
* `Linked Correspondence`
* `Links`
* `Attachments`
* `Activities`
* `Seal Reason`
* `Integrity Hash`
* `Reopened On`
* `Reopened By`
* `Referral Number`
* `To User`
* `Instructions to Recipient`
* `Paper Correspondence`
* `Copy`
* `For Follow-up`
* `Received By`
* `Received On`
* `Completed By`
* `Completed On`
* `Legacy History`
* `Requested By`
* `Requested On`
* `Approval`
* `Approval Level`
* `Decision / Review Note`
* `Approved By`
* `Approved On`
* `Delegator`
* `Delegate`
* `Enabled`
* `Department Scope`
* `Organization Context`
* `Relationship Type`
* `Link Order`
* `Activity Type`
* `Activity On`
* `Actor`
* `Acting For`
* `Delegation`
* `Details`
* `Attachment Type`
* `File`
* `Archive Location`
* `Secret Attachment`
* `File Hash`
* `Party Name`
* `Phone`
* `Entity Type`
* `Code`
* `Clearance Rank`
* `Valid From`
* `Valid To`
* `Active`
* `Higher rank means more restricted correspondence.`
* `Deterministic SHA-256 integrity snapshot; read-only and safe to expose for audit verification.`
* `Main Letter`
* `Attachment`
* `Reply`
* `Reply To`
* `Related To`
* `Parent`
* `Child`
* `Previous`
* `Next`
* `Organization`
* `Created`
* `Registered`
* `Reopened`
* `Status Changed`
* `Sent`
* `In Progress`
* `Rejected`
* `Withdrawn`
* `Returned`
* `Cancelled`
* `Pending`
* `Secret`
* `Confidential`
* `Restricted`
* `Public`
* `Normal`
* `High`
* `Urgent`
* `Letter`
* `Decision`
* `Report`
* `NEW`
* `CORRESPONDENCE`
* `GOVERNANCE`
* `MANAGEMENT`
* `New Correspondence`
* `My Inbox`
* `My Work`
* `Referral Calendar`
* `Referral Gantt`
* `Work Queue`
* `Workflows`
* `Workflow States`
* `User Permissions`
* `Security Health`
* `Employee Productivity`
* `Follow Up Queue`
* `Due Today Referrals`
* `Follow-up Referrals`
* `Total Murasalat Correspondence`
* `Total Murasalat Referrals`
* `Current User`
* `Type`
* `All Visible`
* `My Organization`
* `Delegated to Me`
* `Check`
* `Remediation`
* `Recent Correspondence`
* `Recent Referrals`
* `From`
* `To`
* `Due Date From`
* `Inbox`
* `Search`
* `Actions`
* `Edit`
* `Delete`
* `Print`
* `Email`
* `Share`
* `Comments`
* `Assign`
* `Assigned To`
* `Owner`
* `Created By`
* `Last Modified`
* `Last Edited By You`
* `Timeline`
* `Form`
* `List`
* `Dashboard`
* `Workspace`
* `Calendar`
* `Gantt`
* `Save`
* `Submit`
* `Cancel`
* `Reopen`
* `Return`
* `Review`
* `All`
* `Today`
* `New`
* `Register Correspondence`
* `Close Correspondence`
* `Seal Correspondence`
* `Reopen Correspondence`
* `Send Referral`
* `Receive Referral`
* `Complete Referral`
* `Correspondence was reopened.`
* `Delegator and delegate cannot be the same user.`
* `Delegation end date must be on or after start date.`
* `[Restricted]`
* `DocType is missing.`
* `No native DocPerm rows are configured.`
* `Configure permissions from Role Permission Manager.`
* `No active native Workflow is configured. This is valid: Workflow is optional and entirely controlled from Desk.`
* `Create or activate a Workflow from Settings > Workflow if this document needs governed transitions.`
* `Edit the Workflow in Desk; the application does not enforce a fixed state model.`
* `Active Workflow: {doctype}`
* `Role Permission Manager: {doctype}`
* `PASS`
* `FAIL`
* `WARN`
* `INFO`
* `Updated`
* `Team Work`
* `Productivity`
* `Document`
* `Document Type`
* `Document Number`
* `Document Date`
* `Archive`
* `Barcode`
* `Delivery`
* `Activity`
* `Basic Information`
* `Correspondence Direction`
* `Confidentiality Level`
* `Importance Level`
* `Internal — From / To`
* `Referral Direction`
* `From Department`
* `To Department`
* `From User`
* `Internal department sending the correspondence.`
* `Internal department receiving the correspondence.`
* `Outgoing — From / To`
* `Incoming — From / To`
* `External party receiving the correspondence.`
* `External party that sent the correspondence.`
* `Related Records`
* `Activity History`
* `Audit Security`
* `Body`
* `Reopen Reason`
* `Unsealed`
* `Audit & Security`
* `Originating Department`
* `Sealed By`
* `Correspondence Register`
* `Referral Aging`
* `Follow-up Queue`
* `Arabic Label`
* `Murasalat Correspondence Direction`
* `Cancel Reason`
* `Cancelled By`
* `Cancelled On`
* `Referral Cancelled`
* `Stamp Approval`
* `Clear Approval`
* `مختومة - المرفقات مقفلة`
* `When to use it`
* `What is kept there`
* `Murasalat Management Summary`
* `Murasalat Department Workload`
* `Murasalat Response Times`
* `Completed in Period`
* `Oldest Open (days)`
* `Average Days to Complete`
* `Days to Register`
* `Days to Send a Referral`
* `Days from Send to Receive`
* `Days from Receive to Complete`
* `Days to Close`
* `Measured`
* `{0} assigned a new task {1} {2} to you`
* `Your assignment on {0} {1} has been removed by {2}`
* `Assignment for {0} {1}`
* `Already in the following Users ToDo list:{0}`
* `Shared with the following Users with Read access:{0}`
* `Auto assignment failed: {0}`

Those are Frappe framework strings (`Content`, `Links`, `Actions`, `Delete`, `Email`,
`Comments`, `Assigned To`, `Created By`, `Timeline`, `Dashboard`, `Submit`, `Barcode`,
`Assigned To`, the ToDo-list and sharing notices, `Auto assignment failed`) or generic
Desk phrasing (`Owner`, `Last Modified`, `Dates`, `Identity`, `Team Work`,
`Document Date`, `Document Number`, `Delivery`) that the user sees on Arabic screens.
Deleting them would surface English in the Desk, and that cannot be checked here — so
they stay.

### 2.3 Translation gaps — verified, not introduced

65 strings that the code passes to `_()` have no row in our `ar.csv`.
3 of them are already translated by Frappe itself (`ar.po`), so no
row is needed; the remainder are internal sentinels and report filter labels:

* `15+ Days Late`
* `A completed referral cannot be cancelled; it is already finished.`
* `A reason is required to cancel a referral.`
* `A reason is required to reopen a correspondence, because reopening lifts the integrity seal.`
* `A referral cannot be sent because the Correspondence is closed.`
* `A referral must be sent before it can be completed.`
* `A referral must be sent before it can be received.`
* `A valid Correspondence Direction is required before registration.`
* `Age Band`
* `An approval request cannot be created already approved.`
* `Approved By must be the user recording the decision.`
* `Approved On cannot be recorded without Approved By.`
* `As Of Date`
* `Cancel Referral can only run on Murasalat Referral.`
* `Choose either Department or User, not both.`
* `Clear Approval can only run on Murasalat Approval Request.`
* `Completed Referrals`
* `Correspondence Direction must be Incoming, Outgoing, or Internal.`
* `Correspondence received`
* `Correspondence was reopened. Reason: {0}`
* `Days Late`
* `Draft Referrals`
* `External Date`
* `External No.`
* `Fields from another correspondence direction contain values: {0}. Clear them before saving.`
* `Follow-up`
* `Incoming Receiving Department`
* `Incoming Sender`
* `Integrity seal lifted to allow a documented amendment. Previous snapshot: {0} (sealed on {1} by {2}).`
* `Internal Source Department`
* `Internal Target Department`
* `None of {0} exists on {1}. Available fields: {2}`
* `Only Overdue`
* `Open Correspondence`
* `Open Overdue Referrals`
* `Open Referral Work`
* `Outgoing External Recipient`
* `Outgoing Sending Department`
* `Page Count cannot be negative.`
* `Past Due and Open`
* `Referral {0} was cancelled. Reason: {1}`
* `Referral {0} was completed.`
* `Referral {0} was received.`
* `Referral {0} was sent to {1}.`
* `Related`
* `Sealing`
* `Source Department`
* `Stamp Approval can only run on Murasalat Approval Request.`
* `Target Department`
* `The approval decision is already recorded and cannot be changed.`
* `The correspondence cannot be closed while it has open referrals.`
* `The following fields are required for {0}: {1}`
* `The organizational holder cannot be empty when correspondence is registered.`
* `This writes roles, permissions and Workflows. Re-run with confirm=True.`
* `Unknown inbox scope: {0}`
* `Visible Open Referrals`
* `Within Due Date`
* `Workflow state changed from {0} to {1}.`
* `Worst Lateness (days)`
* `none`
* `unknown`
* `unset`

This branch deleted only strings that nothing referenced, so it introduced no gap:
0 regressions.

## 3. Arabic coverage completed — 65 rows added

AST-based extraction (`.py`) plus strict literal scanning (`.js`, `.html`) showed 65
strings that the code hands to `_()` / `__()` with **no row in `ar.csv`** — they would
have rendered in English on the Arabic Desk: report column labels (`Age Band`,
`Days Late`, `Worst Lateness (days)`, `Within Due Date`, `15+ Days Late`, `Past Due and
Open`, `Completed Referrals`, `Draft Referrals`, `Open Overdue Referrals`,
`Visible Open Referrals`, `Open Referral Work`, `Follow-up`, `Created On`, `Sealing`,
`State`, `External Date`, `External No.`), Desk buttons (`Create`, `Open
Correspondence`, `Related`, `Only Overdue`, `As Of Date`), correspondence field labels
(`Incoming Sender`, `Incoming Receiving Department`, `Outgoing Sending Department`,
`Outgoing External Recipient`, `Internal Source Department`, `Internal Target
Department`, `Source Department`, `Target Department`) and refusal messages from
`services/lifecycle.py`, `services/approvals.py`, `setup/provision.py` and the two
DocType controllers.

All 65 now have reviewed Arabic rows (placeholders `{0}`/`{1}`/`{2}` kept intact), and
`murasalat_office/tests/test_arabic_coverage.py` locks this in: it extracts every
literal the code passes to `_()` / `__()` and fails if any lacks a row.

Verified after the fix: 0 live strings without a row; 0 regressions from the deletions
in §2.2 (computed by diffing message coverage before and after the branch).

## 4. Reviewed and deliberately retained

## 5. Cannot be verified here

* Anything the Desk renders: forms, sidebar, print and PDF output, the notification
  bell, Notification Type muting, scheduler runs.
* Whether `provision.apply` tops up transition tasks on an existing site, and whether
  `readiness()` prints `Ready for users.` there.

## 6. Open

* **The `undefined` seen in the sidebar is still unreproduced.** The sidebar
  (`workspace_sidebar/murasalat_office.json`) has carried `name` and `title` =
  "Murasalat Office" in every commit, every one of its 38 items has a `label`, and
  every `link_to` resolves to a shipped DocType, Report or Workspace. It needs the
  sidebar HTML or the browser console output from the live site.
* The four policy gaps recorded in `docs/NOTIFICATION_REVIEW.md`: a department-targeted
  referral notifies nobody; correspondence `due_date` has no owner; no escalation
  policy; reminder e-mails render in the scheduler's session language.
