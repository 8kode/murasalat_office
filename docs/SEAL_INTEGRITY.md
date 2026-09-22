# Seal integrity and the documented amendment path

A sealed correspondence is the evidentiary record of an official transaction. This
note states what the seal covers, what it refuses, and how a sealed record may still
be corrected.

## What the seal covers

`services/records.py::canonical_payload` defines the snapshot. It includes the identity
and classification fields, the **letter body** (`notes`), its `due_date`, and the
`concerned_person`, plus a per-attachment digest (file, hash, secrecy, type, folder).

The body belongs in the snapshot: a correspondence whose text or deadline can be
rewritten after sealing has no evidentiary value, even if its classification fields are
frozen.

## What is refused

While `record_sealed_on` is set, `validate_immutable_fields` rejects any change to a
field in `IMMUTABLE_AFTER_SEALING`, and `validate_sealed_attachments` rejects any change
to the attachment set. `verify_integrity` fails closed: a record that declares itself
sealed but stores no snapshot is **not** verified.

## The amendment path

There is no silent amendment. Correcting a sealed record means reopening it:

1. **Reopen** (`services/lifecycle.py::reopen_correspondence`) requires a
   `reopen_reason`. The reason is mandatory because reopening lifts the seal.
2. Reopening writes two activity rows: `Reopened` (with the reason) and, when a seal was
   present, `Unsealed` — carrying the **previous snapshot hash, its seal date and the
   sealer** in the activity details, so the earlier form of the record remains provable.
3. The seal fields (`record_sealed_on`, `record_sealed_by`, `integrity_hash`) are cleared.
4. The record is edited and **sealed again**, which produces a new snapshot.

Reopening an open, unsealed record changes nothing (idempotent).

**Policy note:** this is the "documented amendment" option — correction is permitted but
always attributed and always leaves the previous snapshot behind. The stricter
alternative (refuse every amendment, even a documented one) is a one-line change in
`reopen_correspondence`; it has not been taken because official correspondence
occasionally has to be corrected, and an unattributable correction outside the system is
worse than an attributable one inside it.

## Approval attribution

`Murasalat Approval Request.approved_by` / `approved_on` are `read_only` in the DocType,
but **Frappe does not enforce `read_only` server-side** — the metadata alone leaves the
decision forgeable through the API. `_freeze_decision` closes that:

* a request cannot be created already approved;
* `approved_by` must be the acting user, and `approved_on` is stamped from server time
  when the decision is first recorded;
* once recorded, neither value can be changed — no reassignment, no backdating.

## What still needs a running site

These are metadata and logic contracts verified without a bench. Confirming that Desk
renders the `Reopen Reason` field, that the `Unsealed` activity option displays, and that
a real reopen-then-reseal cycle behaves as described requires `bench --site <site> ...`
and is covered by `docs/VERIFICATION.md`.
