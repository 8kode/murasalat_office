# v0.12.0 Access Control & Confidentiality Enforcement

## Security model
Frappe native role permissions remain the baseline. Murasalat adds document-scope and confidentiality checks through `permission_query_conditions` and `has_permission`.

## Important design decision
The `has_permission` hook now returns `None` for ordinary write/create/custom permission decisions so Frappe can continue evaluating native role permissions and v16 Custom Permission Types. Only correspondence scope and confidentiality are explicitly decided here.

## Confidentiality
- clearance rank is derived from currently valid organizational memberships
- list visibility is restricted with permission query conditions
- form/API read is restricted with document permission checks
- `view_confidential` and `download_confidential` are checked as action-specific permissions
- secret attachments are forced to private File storage when the parent correspondence is saved
- a secure attachment access API performs correspondence + attachment-specific authorization

## Verification targets
- confidential document cannot leak through standard list queries
- direct document access checks clearance and organizational scope
- secret attachment requires action-specific permission and clearance
- non-secret attachments inherit parent document read access
- custom referral permissions remain available to Frappe
