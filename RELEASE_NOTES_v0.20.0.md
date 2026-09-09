# Murasalat Office v0.20.0 — Native-Only Frappe/ERPNext Governance

## Objective
Make Frappe 16.34.x / ERPNext 16.34.x Desk the authority for permissions and workflows, with no Murasalat-specific permission policy hidden in application code.

## Changes
- Removed Murasalat `permission_query_conditions` and `has_permission` hooks.
- Removed all Custom Permission Type fixtures and custom action-permission checks.
- Removed hard-coded business roles and administrator policy from application DocTypes.
- Removed code-defined Workflow methods and workflow-state business policy.
- Removed custom correspondence operation buttons and mutation APIs (`close`, `withdraw`, `reopen`, registration/send state mutations).
- Correspondence `workflow_state` is the native workflow field; legacy `status` is retained as hidden compatibility data and is no longer used as workflow policy.
- Referral `status` is editable; normal Frappe DocPerm/User Permissions control who can edit it.
- Removed scheduler-driven referral state mutation.
- Reports now obtain visible correspondence names through permission-aware Frappe list APIs and only then execute SQL projections.
- Governance Health is read-only and reports native Desk configuration; it never creates or changes configuration.

## Important Frappe limitation
Native Frappe Workflow is a DocType-level workflow. A child-table row cannot have an independent native Workflow. Therefore independent referral workflows require promoting Referral to a standalone DocType. This release does not pretend that application code can provide that missing native capability.

## Verification
- Static tests must pass outside Frappe.
- JSON parsing and Python compilation must pass.
- Final integration verification must run on a real Frappe 16.34.x + ERPNext 16.34.x Bench.
