# Murasalat Office v0.18.8 — Deep Security Hardening

This release is a corrective follow-up to v0.18.7 after a file-by-file review of the application.

## Security fixes
- Permission-query visibility is now clearance-constrained for users both with and without organization memberships.
- Users without organizations can still see records they own, currently hold, or are explicitly referred to, subject to confidentiality clearance.
- Custom operational permission types (`close`, `withdraw`, `reopen`, and referral actions) now fail closed outside the document business scope while still delegating role permission decisions to Frappe.
- Classified correspondence attachments are treated as restricted even if legacy attachment rows have `is_secret=0`.
- User referrals now require a user recipient and organization referrals require an organization recipient; mixed/invalid recipient data is rejected.
- Referral numbers are validated for uniqueness within a correspondence.
- Organization-scoped delegations now use the actor's active organization when referral actions are authorized.
- Approval requests cannot spoof `requested_by` and the requester cannot approve/reject their own request.
- Workflow transitions disable self-approval.

## Reliability fixes
- Referral activity synchronization now occurs before the parent save so generated activity rows are persisted reliably.
- Version bumped to 0.18.8.
- Security contract tests expanded to cover clearance-constrained list queries, scoped custom actions, and user-referral visibility.

## Validation
- Python source was syntax-checked with `ast.parse`/`compileall`.
- JSON metadata remains parseable.
- The application must still be tested inside a real Frappe/ERPNext v16 bench because Frappe itself is not installed in this build environment.
