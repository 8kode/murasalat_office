## v0.27.3

- Remediated the expert review findings while preserving Native-First governance.
- Added readable Approval Request (`MAR-.#####`) and Membership (`MOM-.#####`) naming for new records.
- Added Delegation change tracking and a composite membership uniqueness guard.
- Exposed governance health through a System Manager-only API.
- Extended delegated Inbox handling to explicit organization-targeted referrals.
- Added real Correspondence lifecycle activity events and removed dead activity types.
- Unified attachment hashing and made the integrity hash visible/read-only for audit.
- Corrected productivity overdue and date-boundary calculations.
- Added Work Queue summaries and safer restricted-subject report UX.
- Batched legacy migration parent checks and hardened legacy index naming.
- Added framework-light regression coverage for the new contracts.

# Murasalat Office

Murasalat Office is a metadata-first correspondence management application for the Frappe Framework, designed to integrate cleanly with ERPNext when it is installed.

## Design principle

The application deliberately uses native Frappe/ERPNext governance:

- Role Permissions Manager owns access control.
- User Permissions and sharing remain native Frappe mechanisms.
- Workflows and Workflow States are created and maintained from Desk.
- Assignment Rules, ToDos, Notifications and Workflow Actions remain configurable in Desk.
- No business roles, workflow definitions, permission rows or custom permission types are shipped.
- `Murasalat Referral` is a standalone DocType so every referral can have its own native Workflow.
- Correspondence-to-Referral navigation uses native Connections.

## Native UX

The app exposes standard Frappe views and navigation:

- Form + Timeline
- List
- Connections / Linked With
- Calendar
- Gantt
- Kanban (when configured by administrators)
- Report Builder / Script Reports
- Workspace Shortcuts and Quick Lists
- Native Number Cards
- Assignments / ToDos
- Workflow Actions
- Notifications
- Awesomebar / Search

## Version

v0.27.3 — Expert-review remediation release, preserving Native-First governance.

Target baseline: Frappe 16.33.x. ERPNext 16.34.x is supported when present, but is not a runtime dependency.
