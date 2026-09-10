# Murasalat Office v0.22.1

Metadata-first correspondence management for **Frappe Framework 16 / ERPNext 16**.

## Architecture principle

**Frappe/ERPNext Desk is the control plane.** Murasalat Office provides DocTypes, data integrity, reporting projections, and business data validation. It does not own a parallel permission engine or workflow state machine.

### Permissions

All document authorization is configured from native Frappe/ERPNext interfaces:

- Role Permission Manager
- User Permissions
- Permission Levels
- Role Profiles / Roles
- Share / assignment features provided by Frappe/ERPNext
- Customize Form for field metadata

The app ships no business-role fixtures, DocPerm rows, permission hooks, or custom action-permission policy.

### Workflows

`Murasalat Correspondence`, `Murasalat Approval Request`, and `Murasalat Referral` are normal DocTypes with a `workflow_state` field. Each can have an independent native Frappe Workflow configured from **Settings → Workflow**.

You can add, remove, rename, reorder, or redesign Workflow States and Transition Rules from Desk without changing the application code. The app does not interpret particular state names as authorization rules.

### Referral architecture

`Murasalat Referral` is a **standalone DocType**, not a child-table row. This allows every referral to have its own native Workflow, permissions, User Permissions, and audit trail.

### Reports

Reports may use SQL for projections, but every exposed DocType is first constrained through Frappe's permission-aware `get_list` API. This is necessary because raw SQL / `get_all` does not automatically apply the same document visibility semantics as `get_list`.

### What remains in application code

The remaining server-side code is limited to data integrity and data validation that is not a permission/workflow policy, for example:

- required relationships and mutually exclusive recipient fields
- duplicate/self-link validation
- date consistency validation
- attachment hashing and integrity verification
- read-only audit/projection helpers
- one-time migration of legacy referral rows

These checks do not decide which Role may perform an action or which Workflow transition is allowed.

## Desk governance

See `docs/NATIVE_ONLY_GOVERNANCE_v0.22.0.md` for the operational governance model and `docs/DESK_GOVERNANCE_v16.34.md` for the Frappe/ERPNext Desk configuration checklist.

## Verification

The release includes static contract tests, JSON validation, Python compilation, report-reference checks, and package hygiene checks. Full runtime integration testing must be executed inside a real **Frappe 16.34.x + ERPNext 16.34.x Bench**, because the current development environment does not contain the Frappe runtime.
