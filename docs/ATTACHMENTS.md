# Attachments

A record's files live in the **Attachments table** (`Murasalat Attachment`) on both
`Murasalat Correspondence` and `Murasalat Referral`. It is the only list a reviewer reads, and
the only one that says **what** a file is and **where its paper original is filed**.

## What the framework does, and what this app adds

Frappe has exactly one way to attach a file to a document: a `File` row carrying
`attached_to_doctype` and `attached_to_name`. The panel in the form sidebar, drag-and-drop, the
REST endpoint and a row's own Attach control all go through it. Everything below is therefore
Frappe's, not ours:

| Concern | Frappe's own mechanism |
| --- | --- |
| Storage, public and private | `File.is_private` → `/files/` or `/private/files/` |
| **Permissions** | `File.has_permission` defers to the attached record - and `get_permission_query_conditions` does the same for lists, so a user who cannot read a correspondence cannot read its attachments |
| Duplicate detection | `content_hash` recorded on every upload; `File.validate_duplicate_entry` refuses the same content twice on the same document |
| Folders | `File.folder`, `is_folder`, `is_home_folder` |
| Change tracking | `track_changes` on `File` |
| Deletion | `File.on_trash` |

This app adds only the three things the framework cannot express:

1. **What a file is** → `attachment_type`
2. **Where the paper original is filed** → `archive_location`
3. **Integrity** → `file_hash` per row, and the record's own seal

## How a file gets into the table

Two `File` events are registered through the framework's own `doc_events` hook
(`hooks.py` → `services/attachment_index.py`):

| `File` event | What it does |
| --- | --- |
| `before_insert` | Refuses the file when the record is sealed |
| `after_insert` | Appends a row for a record-level upload, defaulting to type `Attachment` |

One signal separates the two kinds of upload: **`attached_to_field`**.
`frappe/client.py::attach_file` sets it from the `docfield` argument, so it is empty for an
upload aimed at the record and holds the field name when the user uploaded into a specific
field. A field upload is the user filling that row themselves, so it is left alone.

The row is written through the DocType's own controller (`append` then `save`), so the seal
guard, the file hash and the uploading user's write permission all still apply. Nothing writes a
child table directly.

An upload that cannot be filed does **not** abort the upload: the file is already stored and the
seal covers it through the linked-file snapshot. The failure is logged and the backfill picks
the file up on the next migrate.

## How the table and the panel stay in step

The File event files the row server-side, so the open form has to learn about a row it never
created. It wraps `frappe.ui.form.Attachments.attachment_uploaded` - the method the panel runs
for every completed upload - and merges the server's rows into `frm.doc.attachments`.

Two framework facts decide that design, both read from the Frappe v16 source:

| Fact | Consequence |
| --- | --- |
| `Document.update_child_table` **deletes every child row the submitted document does not contain** | A form that never learned about the row would erase it on the next save, so the refresh is a correctness requirement, not a convenience |
| The panel hands `frappe.ui.FileUploader` its own `on_success` and never reads one set on the control (`sidebar/attachments.js`) | A hook on `on_success` would never fire; the wrap delegates to the original method |

The merge is **additive**: an unsaved row is kept as it is, and a row from the server is copied
without `__islocal` so saving does not insert it twice. The form is never reloaded, so nothing
typed is discarded.

## The vocabulary is master data

| Table | Holds | Seeded codes |
| --- | --- | --- |
| `Murasalat Attachment Type` | what a file is | `Main Letter`, `Attachment`, `Reply`, `Copy for Information`, `Translation` |
| `Murasalat Archive Location` | where the paper original is filed | `Correspondence Office`, `Central Archive`, `Department Shelf`, `Director Office` |

Neither table ships permission rows - access is site configuration, as it is for every other
table in this app. `governance_plan.materialize` grants every role **read** on both, because a
Link field cannot resolve a record the user may not read; a site that set its permissions up by
hand grants the same two read rights from **Role Permission Manager**. Seeding needs neither:
`master_data.seed` registers as an administrator.

Both are ordinary DocTypes: a site adds a value, changes its display name, or disables it from
Desk with **no code change and no upgrade**. The stored value is a short English code and the
displayed name is Arabic, which is what `title_field` is for - so a Link reads
*الخطاب الأصلي* while the record stores `Main Letter`.

Codes are never renamed: `allow_rename` is off, because renaming a code would orphan every
record that stored it.

The three codes already recorded by the old `Select` field are among the seeded ones, so
existing rows keep resolving without a data migration.

## The rules the table keeps

* `attachment_type` is required and defaults to `Attachment`.
* `archive_location` is **optional**. It replaced a free-text field named `folder`, which
  collided with Frappe's own folder concept and collected values like `dfs` and `نن`. An empty
  location is honest; an invented one is not.
* `file_hash` is read-only, written automatically.
* A sealed record takes **no new attachments**, refused in `File.before_insert` - so the rule
  holds for the REST endpoint and drag-and-drop too, not only for a button somebody might have
  hidden. Reopen the record first.
* The seal covers the attachment rows **and** every `File` linked to the record, so a file added
  outside the table is still inside the seal.

## Files uploaded before indexing existed

Files attached through the panel or the old gallery carry no row. They are already covered by
the seal, but they are invisible in the table and carry no type. Read-only plan first:

```bash
bench --site <site> execute murasalat_office.services.attachment_index.plan_indexing
```

It reports four groups: `create`, `already_indexed`, `sealed` (left alone - a sealed record's
stored hash covers its rows, so writing one would fail the check on a record nobody touched), and
`orphaned`. `bench migrate` then runs the backfill and prints exactly what it wrote.

## Migrating to this vocabulary

`bench migrate` runs two patches, in this order:

1. **`v0_24_rename_attachment_folder`** (before the schema sync) renames the column
   `folder` → `archive_location`, carrying the values across rather than dropping them.
2. **`v0_25_attachment_vocabulary`** (after the schema sync) seeds both tables, then reconciles
   what the records already hold:
   * a value that is not a known location is **cleared and printed** with its parent record, and
     is re-filed by hand. It is cleared rather than kept because a Link field is validated on
     save, so a dangling value would block the next save of that correspondence;
   * an unknown attachment type is **reset to `Attachment`** and printed, since the field is
     mandatory and `Attachment` is the generic code for an accompanying paper.
3. **`v0_26_index_record_attachments`** (also after the schema sync) runs *after* the vocabulary,
   not in numeric order: it writes rows whose attachment type is a Link, so the types have to
   exist first. It is idempotent and skips sealed records.

## Still open

* Retention and disposal periods. They belong on the correspondence type, not on the attachment
  row, and need the office's statutory periods.
* No attachment versioning: replacing a file means a new row.
