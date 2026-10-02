# Murasalat Office v0.27.4 — Core Cleanup

## Purpose

This release is a source-level cleanup of the approved v0.27.3 baseline. It removes
obsolete custom governance models and retired projections without changing the core
Correspondence / Referral architecture.

## Removed

- `Murasalat Approval Request` DocType and its controller/dashboard/test files.
- `services/approvals.py` and the `Stamp Approval` / `Clear Approval` lifecycle hooks.
- `Murasalat User Organization Membership` DocType and its validation/test files.
- The custom `My Organization` inbox scope, which depended exclusively on Membership.
- The retired `current_holder_user` projection from Correspondence.
- Workspace and governance references to the removed models.
- Obsolete phase/audit documentation that no longer describes the maintained tree.

## Preserved deliberately

- Native Frappe Workflow for Correspondence and independent native Workflow for Referral.
- Existing `approval_entity` field on official outgoing letters; this is document metadata,
  not a custom approval-request system.
- Historical migration patches required for upgrade compatibility, including `legacy_history`.
  They are migration compatibility code, not active runtime features.
- Native permissions, Assignment/ToDo, Notifications, File, sealing and integrity controls.

## Important

Removing a DocType from the source tree does not automatically delete an already-installed
DocType or its database table on an existing site. Existing sites must be reviewed before
database cleanup. No destructive automatic migration is shipped by this release.
