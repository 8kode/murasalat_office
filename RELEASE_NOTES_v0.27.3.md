# Murasalat Office v0.27.3 — Expert Review Remediation

## Core hardening

- Approval Request naming: `MAR-.#####`.
- Delegation change tracking enabled.
- Membership dead clearance metadata removed; new membership naming uses `MOM-.#####`.
- Composite `(user, organization)` uniqueness enforced through a defensive post-migrate database index.
- Correspondence immutable-field terminology corrected to sealing.
- Integrity hash made visible/read-only.
- Attachment hashing centralized.

## Operational behavior

- Governance health exposed through a System Manager-only API.
- Scoped delegation now includes explicitly delegated organization-targeted referrals.
- Employee productivity overdue logic uses completion time for completed referrals.
- Work Queue now returns a native summary.
- Operational summary date handling is database-type safe.

## Activity and migration quality

- Correspondence Activity now exposes only events actually emitted by the application and records status/seal/reopen transitions.
- v0.21/v0.22 migrations batch parent existence checks instead of issuing one existence query per row.
- Legacy child-table parent index receives a collision-resistant name.

## Validation

- Framework-light tests cover the new API contract, lifecycle activity, membership cleanup, shared hashing, restricted-report UX, and delegated organization behavior (59 tests).
- Full Bench integration remains a target-site gate.
