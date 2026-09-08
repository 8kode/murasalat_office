# Murasalat Office v0.12.0

Metadata-first correspondence management for Frappe Framework 16 / ERPNext 16.


## v0.13.0
- Record sealing and SHA-256 integrity snapshots.
- Immutable identity/classification fields after registration.
- Close guard against open referrals.
- Reopen audit timestamps while retaining history.

## v0.15.0 — Native Registration Journey

This release introduces a server-enforced registration journey that follows the operational pattern:

1. Data
2. Attachments
3. Referrals
4. Registration
5. Sending

The implementation deliberately keeps Frappe as the primary UI and permission engine. Custom code only enforces cross-field and lifecycle rules that cannot be represented safely by field configuration alone.

### Registration gates

- Internal: target entity or at least one referral
- Incoming: source entity, external letter number and date
- Outgoing: target entity
- All types: subject, transaction type, confidentiality, importance, at least one attachment and a Main Letter attachment

### Lifecycle actions

- Registration Checklist
- Register Correspondence
- Send Referrals

Registration sealing is executed in `before_save`, ensuring integrity metadata is persisted in the same document transaction.

## v0.18.0 — Operational Experience Layer
- Added **Murasalat My Work** as a referral-centered personal work queue.
- Added **Murasalat Due Today** for operational due-date focus.
- Added **Murasalat Follow Up Queue** for referrals explicitly marked for follow-up.
- The new reports use the existing Referral records as the source of truth; no duplicate inbox or analytics DocTypes were introduced.
- The work model is deliberately: Correspondence = institutional record, Referral = actionable work unit, ToDo = optional personal notification.
