# v0.13.0 – Document Lifecycle & Records Integrity

This release adds native-DocType lifecycle controls while preserving Frappe Version, Timeline and Workflow capabilities.

## Controls
- Seal registered records with a canonical SHA-256 snapshot.
- Prevent identity/classification changes after registration.
- Block closure while open referrals exist.
- Record reopen actor/time without deleting history.
- Preserve attachment hashes inside the integrity payload.

## Native Frappe/ERPNext strategy
Use standard DocType Version/Timeline, Workflow, ToDo assignment, File privacy and role permissions before adding custom automation.
