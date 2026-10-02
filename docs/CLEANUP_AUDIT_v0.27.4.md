# Murasalat Office — Cleanup Audit v0.27.4

## Baseline reviewed

`v0.27.3` supplied by the project owner.

## Core DocTypes reviewed

The maintained core remains:

- Murasalat Correspondence
- Murasalat Referral
- Murasalat Correspondence Activity
- Murasalat Correspondence Link
- Murasalat Attachment
- Murasalat Attachment Type
- Murasalat Archive Location
- Murasalat Delegation
- Murasalat External Party
- Murasalat External Party Type
- Murasalat Transaction Type
- Murasalat Confidentiality Level
- Murasalat Importance Level
- Murasalat Correspondence Direction
- Murasalat Referral Direction

## Removed as obsolete

### Murasalat Approval Request

It duplicated native Frappe Workflow governance. Its decision model was also incomplete:
the custom record did not provide an independent rejection outcome while the application
already delegated Workflow authority to Desk. Its controller, dashboard, service, hooks,
governance permissions, overview panels and tests were therefore removed.

### Murasalat User Organization Membership

It was used only to implement the `My Organization` branch of the Referral Inbox and
to maintain a custom user/department relationship. That relationship is not part of the
Correspondence/Referral domain model. The custom Inbox scope and its database uniqueness
machinery were removed rather than preserving a second organization-membership system.

### current_holder_user

This field was already a retired projection and was explicitly not the source of personal
assignment. Referral + native Assignment/ToDo are the authoritative work-unit model.
The dead projection was removed.

## Deliberately retained

`legacy_history` and the v0.21/v0.22 migration patches remain because they are upgrade
compatibility material for sites that may still carry the former referral structure.
They are not runtime business logic.

`approval_entity` remains because it is metadata on an official outgoing letter and is
not an Approval Request DocType.

## Verification performed

- Source references to the removed DocTypes were eliminated.
- Removed workflow hooks were eliminated.
- Overview/dashboard/governance/inbox references were eliminated.
- Retired `current_holder_user` references were eliminated.
- Historical migration compatibility was kept intact.
- Framework-light test suite was rerun after cleanup.
