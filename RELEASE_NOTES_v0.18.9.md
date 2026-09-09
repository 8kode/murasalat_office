# Murasalat Office v0.18.9 — Native Desk Governance

## Governance model
- Frappe/ERPNext Desk is now the authoritative UI for role assignment, document permissions, custom action permissions, and workflow configuration.
- Removed Role, Workflow, and Workflow State fixtures from the app migration path so administrator changes are not overwritten by upgrades.
- Retained only developer-defined Permission Type fixtures, as required for Frappe v16 custom permission types.
- Removed hard-coded Murasalat business roles from the privileged security bypass. Only `Administrator` and `System Manager` are platform-level bypass users.
- Removed app-registered custom workflow methods; standard Frappe Workflow transitions are now the supported control plane.

## Workflow
- `Murasalat Approval Request` no longer assumes fixed states such as Draft/Under Review/Approved/Rejected.
- Workflow changes are recorded generically in the correspondence activity log.
- Final-state handling uses the standard `Workflow State.doc_status = 1` convention rather than hard-coded state names.

## Compatibility
- Target: Frappe 16.34.x
- Target: ERPNext 16.34.x
- `required_apps = ["erpnext"]` added.

## Validation
- Python syntax and JSON metadata should be validated before installation.
- Full tests must run inside a real Frappe/ERPNext 16.34.x bench.
