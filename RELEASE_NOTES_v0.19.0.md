# Murasalat Office v0.19.0

## Desk Governance Operations

- Added `Murasalat Security Health` read-only governance report.
- Added reusable governance validation service and whitelisted health endpoint.
- Added governance links to the Murasalat Office workspace.
- Added static contracts ensuring governance code does not mutate Roles/Workflows/Permissions.
- Added administrator operations guide.
- Version bumped to 0.19.0.

## Design principle

Roles, Role Permission Manager configuration, Custom Permission Type assignments, Workflow, Workflow State, and User Permissions remain site-admin controlled through Frappe/ERPNext Desk. The app validates the resulting configuration but does not overwrite it during upgrades.
