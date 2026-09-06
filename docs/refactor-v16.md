# Murasalat Correspondence v16 Native Refactor

## Architecture

The correspondence form now relies on Frappe metadata and standard Desk UI:

- `depends_on` for direction-specific sections.
- `mandatory_depends_on` for conditional letter requirements.
- `read_only_depends_on` for post-registration immutability.
- Workflow for correspondence and referral actions.
- Connections / linked documents for correspondence documents and referrals.
- Standard Timeline, Attachments, List View, Print, and Workflow actions.

No DocType JavaScript remains in the application.

## Numbering

`Murasalat Correspondence` uses an internal random document name while it is a draft.
The official `correspondence_number` is issued in `before_submit`, when the Register
workflow action submits the document. The custom server logic remains because the current
requirements combine:

- issuance only at registration,
- per-rule sequences,
- optional Hijri year,
- and a sequence that may be independent per correspondence type without exposing the
  internal series key in the public number.

## Referrals

`Murasalat Referral` uses `workflow_state` as its single business state.
The old custom API action methods were removed. Standard Workflow actions drive the UI.
Python only validates dynamic recipient authorization and writes transition timestamps.

## Migration

Run:

```bash
bench --site <site> migrate
bench --site <site> clear-cache
bench build --app murasalat_office
bench --site <site> clear-cache
```

The included post-model-sync patch removes the legacy Client Script and migrates existing
referral status values when the old column is still present.
