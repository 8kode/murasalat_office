# Expert Audit — Murasalat Office v0.27.3

## Release posture

v0.27.3 applies the actionable findings from the v0.27.2 expert review while preserving the Native-First architecture.

### Implemented

- Added readable `MAR-.#####` naming for Murasalat Approval Request.
- Renamed `IMMUTABLE_AFTER_REGISTRATION` to `IMMUTABLE_AFTER_SEALING` and aligned the validation message.
- Exposed read-only `governance_health()` through a System Manager-only whitelisted API.
- Added `track_changes: 1` to Murasalat Delegation.
- Added Work Queue summary data.
- Batched legacy migration parent-existence checks in v0.21/v0.22.
- Renamed the legacy child-table parent index to `murasalat_child_parent_idx`.
- Added a best-effort composite unique database index for User Organization Membership `(user, organization)` to close concurrent-insert races.
- Removed unused `access_level` and `max_clearance_rank` fields from the Membership DocType because the app intentionally does not implement a clearance/role engine.
- Changed Membership naming to readable `MOM-.#####` for new records; existing names remain unchanged.
- Made `referral_number` explicitly unique, matching its generated document name.
- Made `integrity_hash` visible/read-only for audit transparency.
- Expanded `notes` and `seal_reason` to `Text`.
- Unified attachment file hashing in `services.records.hash_file_url`.
- Corrected `operational_summary()` date comparisons with `getdate()`.
- Corrected employee productivity overdue semantics to compare due date with completion time for completed referrals and made the `to_date` boundary exclusive of the next day.
- Extended scoped delegated Inbox handling to include organization-targeted referrals for explicitly delegated organizations, while unrestricted delegation remains limited to direct User referrals.
- Reduced Correspondence Activity options to the lifecycle events the controller can actually emit: Created, Status Changed, Sealed, Reopened.
- Added lifecycle activity emission for workflow-state changes, sealing, and reopening.
- Isolated framework-light test module stubs so they do not leak through `sys.modules`.

## Deliberately not implemented

- `concerned_person` remains free text because the domain may include external persons and the app does not ship a Contact/Person master. Converting it to User would incorrectly exclude external parties and would be a business-policy decision.
- Automatic disabling of expired Delegation rows was not added. Current Inbox queries already enforce enabled/date validity, while persisting `enabled=0` would require a scheduler or mutation policy outside the Native-First governance contract.
- Attachment type was not converted into a new master DocType; the current three values are data classification, not authorization.
- A bespoke API rate limiter was not added. Explicit integrity verification is permission-checked and intentionally expensive; rate limiting is better handled at the platform/reverse-proxy layer if operationally required.
- Full Bench integration remains the deployment gate because this build environment does not contain Frappe/ERPNext runtime.

## Architecture result

The release remains Native-First: no hardcoded roles, workflow states, permission-query hooks, or shipped governance fixtures. Application code uses Frappe permission-aware APIs and does not create a parallel authorization engine.

## Verification snapshot

- Framework-light regression suite: **59 passed**.
- JSON validation: **26 files, 0 errors**.
- JavaScript syntax: **10 files, 0 errors**.
- Runtime direct SQL scan: **0 hits** outside the legacy patch layer.
- Custom permission hook scan: **0 hits** outside tests.
- Release archive contains **167 entries** and no cache/bytecode artifacts.
- Archive re-extraction: **59 tests passed** and JSON validation passed.

The SHA-256 is published with the release archive artifact itself.
