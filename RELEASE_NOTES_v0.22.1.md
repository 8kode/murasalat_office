# Murasalat Office v0.22.1 — Final Expert Hardening

Patch release following the v0.22.0 expert review.

## Fixed

- Enabled `track_changes` on standalone `Murasalat Referral` documents.
- Corrected `.eslintrc` JSON syntax so JavaScript lint configuration is valid.
- Removed the duplicate referral-count database query from `Murasalat Correspondence.on_update`.
- Rejected attachment-set changes after a correspondence is sealed, with an explicit user-facing validation message.
- Automatically initializes the SHA-256 integrity snapshot when a correspondence is first sealed, so the integrity mechanism cannot remain inert simply because no hash was previously populated.
- Simplified `Murasalat Approval Request.validate` ordering for new-document initialization and immutable-field checks.
- Removed unused session-user values from reports that do not filter by user.
- Corrected employee productivity date filters to use `completed_on` only; incomplete referrals are no longer classified by arbitrary `modified` timestamps.
- Made report permission parameter keys alias-specific to avoid future collisions when the same DocType is constrained more than once.

## Governance and scalability

- Retained the native Desk governance architecture: no application-owned permission engine, workflow engine, role fixtures, permission fixtures, or workflow fixtures.
- SQL reports continue to use Frappe permission-aware `get_list` projections for visibility. This preserves the native-governance contract without introducing a custom `permission_query_conditions` hook. Large installations should validate report query-size behavior with their production data volume before rollout.

## Verification

The release is intended for deployment to a real Frappe 16.34.x / ERPNext 16.34.x Bench for final runtime/UAT validation. Static, structural, syntax, migration, and package-hygiene checks are included in the release test suite.
