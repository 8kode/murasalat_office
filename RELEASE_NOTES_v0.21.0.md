# Murasalat Office v0.21.0 — Standalone Referral / Native Workflow

## Main architectural change

`Murasalat Referral` is now a standalone Frappe DocType instead of a child table. Each referral has a Link to `Murasalat Correspondence` and its own `workflow_state`.

This makes each referral a first-class Frappe document that can have its own native Workflow, Workflow State, Transition Rules, roles, conditions, and document permissions from Desk. No referral status machine is hard-coded in the application.

## Removed from code

- Legacy referral `status` state machine.
- Hard-coded open/closed referral states.
- Child-table parent/parenttype dependency in operational reports.
- Referral lifecycle transitions implemented in Python.
- Automatic ToDo/escalation lifecycle tied to referral status.
- Correspondence child-table referral validation/synchronization.

## Native Frappe/ERPNext control

Administrators can create or change the Referral Workflow from **Settings → Workflow**, define arbitrary states and transitions, choose roles, conditions, and update fields, without changing application code.

Document permissions for `Murasalat Referral` are controlled by **Role Permission Manager**, User Permissions, Permission Levels, and standard Frappe mechanisms.

## Migration

A one-time Frappe patch migrates legacy child referrals into standalone Referral documents and maps the previous status value into `workflow_state` as historical data. The old child-table columns are not used by the application. Frappe schema synchronization treats removed fields as soft-deleted.

## Verification

- Static governance tests: 10 passed.
- Python compilation: passed.
- Native Workflow field present on Referral.
- Referral is no longer a child table.
- No hard-coded referral status states remain in application Python/JS/report code.

Full integration testing must be run inside a real Frappe 16.34.x + ERPNext 16.34.x Bench.
