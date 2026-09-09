# Native-Only Governance — v0.22.0

## Principle

Murasalat Office does not implement a second authorization or workflow engine. **Frappe/ERPNext Desk is authoritative.**

## Permissions

Configure access from:

1. Role Permission Manager
2. Roles / Role Profiles
3. User Permissions
4. Permission Levels
5. Share / assignment features provided by Frappe/ERPNext
6. Customize Form for field metadata

The application does not ship DocPerm rows, business roles, permission-query hooks, `has_permission` hooks, or custom action-permission policy.

## Workflow

Native Workflow is optional and entirely site-admin controlled. Apply it independently to:

- Murasalat Correspondence
- Murasalat Approval Request
- Murasalat Referral

`Murasalat Referral` is a standalone DocType specifically so each referral can have its own native Workflow.

Workflow States, Transition Rules, Roles, Conditions, Allow Self Approval, and other native Workflow settings are configured from Desk. No state name is hard-coded in application policy.

## Reporting security

Script Reports that use SQL first obtain visible document names through Frappe's permission-aware `get_list` API for every exposed governed DocType. They then constrain the SQL projection by those names.

## Application validation

Server-side validation remains only for data integrity. Validation is not used to decide roles, permissions, or Workflow transitions.

## Upgrade behavior

The app does not ship Role, Workflow, Workflow State, or DocPerm fixtures. Site administrators therefore retain control over governance configuration across app upgrades.

## Verification

Run the app's static tests and then perform runtime integration tests inside a Frappe 16.34.x + ERPNext 16.34.x Bench.
