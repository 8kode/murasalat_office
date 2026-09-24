# Attachments: one source of truth

A record's files live in the **Attachments table** (`Murasalat Attachment` child table) on both
`Murasalat Correspondence` and `Murasalat Referral`. It is the only list a reviewer reads, and
the only one that says **what** a file is: its type, where the paper original is filed, whether
it is secret.

## How a file gets into the table

Frappe has exactly one way to attach a file to a document: a `File` row carrying
`attached_to_doctype` and `attached_to_name`. Every door goes through it - the form's sidebar
panel, drag-and-drop, the REST upload endpoint, a row's own Attach control. So the app listens
there instead of replacing any of it, through the framework's own `doc_events` extension point
(`hooks.py` → `services/attachment_index.py`):

| `File` event | What it does |
| --- | --- |
| `before_insert` | Refuses the file when the record is sealed |
| `after_insert` | Appends a row for a record-level upload, defaulting to type `Attachment` |

One signal separates the two kinds of upload: **`attached_to_field`**.
`frappe/client.py::attach_file` sets it from the `docfield` argument, so it is empty for an
upload aimed at the record and carries the field name when the user uploaded into a specific
field. A field upload is the user filling that row themselves; indexing it too would file the
same file twice. So a field upload is left alone, and a record-level upload is filed.

The row is written through the DocType's **own controller** (`document.append(...)` then
`save()`), so the duplicate check, the seal guard, the `file_hash`, and the uploading user's
write permission all still apply. Nothing writes a child table directly.

## What was tried first, and why it changed

The first attempt deleted the `Attachment Gallery` field and **hid Frappe's sidebar panel**
with a DOM selector, so the table would be the only visible list. The gallery deletion stands -
that field is in Frappe's `no_value_fields` and `display_fieldtypes`, so it stores **no column
at all** and removing it loses no data. The panel hiding was withdrawn:

| Approach | Why |
| --- | --- |
| Gallery field - **removed** | A second list of the same files recording nothing about them |
| Panel hidden by DOM selector - **withdrawn** | Reached into markup Frappe does not publish, and worked *against* the framework instead of with it |
| Custom upload button - **removed** | A third upload affordance; the panel is the framework's own, and it now feeds the table |
| Panel left intact - **kept** | Native, and no longer a second list: its uploads become table rows |

## The rules the table enforces

* `attachment_type` is a controlled vocabulary - `Main Letter`, `Attachment`, `Reply` - and
  defaults to `Attachment`.
* `folder` is **optional**. It used to be required free text, which produced values like "نن"
  typed by somebody who had to put something there. An empty folder is honest; an invented one
  is not.
* The same file cannot be recorded twice under the same type
  (`services/records.py::validate_attachment_rows`, called from both controllers).
* `file_hash` is read-only, written automatically.
* A sealed record takes **no new attachments**, refused in `File.before_insert` - so the rule
  also holds for the REST endpoint and drag-and-drop, not only for a button somebody might
  have hidden. Reopen the record first.

## Files uploaded before this existed

Files attached through the panel or the gallery carry no row. They are already covered by the
integrity seal - the hash reads the linked `File` rows as well - but they are invisible in the
table and carry no type. To see what the backfill would do, **read-only, before migrating**:

```bash
bench --site <site> execute murasalat_office.services.attachment_index.plan_indexing
```

It reports four groups: `create` (a row will be written), `already_indexed`, `sealed` (left
alone - see below), and `orphaned` (a `File` whose record no longer exists). Then
`bench --site <site> migrate` runs
`patches/v0_23_index_record_attachments.py`, which prints exactly what it wrote. It is
idempotent, so re-running after a partial failure is safe.

**Sealed records are deliberately skipped.** Their stored hash covers their rows, so writing
one would fail the seal check on a record nobody tampered with. Their files stay covered by the
linked-`File` snapshot.

## Still open

* `folder` is free text. Making it a controlled list would be better, but it needs the
  archive's actual location names and a migration for existing values.
* `is_secret` hides a file's **name** in the overview and the print formats. It does not restrict
  access to the `File` document itself - that is governed by Frappe's own File permissions.
* The panel refresh relies on the native `Attachments` control accepting an `on_success`
  callback. If it does not, the new row appears on the next form reload instead - a cosmetic
  delay, not a lost row.
