# Murasalat Office v0.22.0

## Final native-governance cleanup

- Removed unused Murasalat permission-policy namespace.
- Removed unused registration/lifecycle API and service.
- Removed unused custom escalation-policy DocType.
- Removed delegation action-permission flags (`allow_*`); native permissions and Workflow are the governance mechanisms.
- SQL reports now enforce native Frappe visibility for both `Murasalat Correspondence` and standalone `Murasalat Referral`.
- Operational summary no longer assumes fixed workflow states such as Completed/Rejected/Returned.
- Removed stale legacy governance references from the Workspace.
- Bumped application version to 0.22.0.

## Verification

Static tests, JSON validation, Python compilation, package hygiene, and ZIP integrity are required before release. Full runtime integration tests require a real Frappe 16.34.x + ERPNext 16.34.x Bench.


## Superseded architecture

Earlier release notes document the application's historical permission/lifecycle implementations. Those mechanisms are not part of v0.22.0 runtime governance.
