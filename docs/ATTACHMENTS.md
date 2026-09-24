# Attachments: one source of truth

A record's files live in the **Attachments table** (`Murasalat Attachment` child table) on
both `Murasalat Correspondence` and `Murasalat Referral`. Nothing else lists them.

## Why the other two entry points were removed

The form used to offer three ways to attach a file, and they disagreed with each other:

| Source | What it recorded | Covered by the seal |
| --- | --- | --- |
| Attachments table | type, folder, secret flag, file hash | yes — this is what `canonical_payload` hashes |
| `Attachment Gallery` field | nothing but the file | no metadata at all |
| Frappe's sidebar attachments panel | nothing but the file | only after linked files joined the snapshot |

Only the table says **what** a file is and **where the paper original is filed**, and only
the table's rows feed `file_hash`. The gallery could not record a type, a folder or
secrecy; the sidebar panel showed the same files a second time with no classification. A
user who uploaded through either had no way to say which paper it was, and a reviewer had
no way to tell whether the file belonged to the record at all.

So the gallery field was deleted from both DocTypes and the sidebar panel is hidden by each
form's script. Uploads happen through the table:

* the native **Attach** control on a row, which uploads and fills the row, or
* the **رفع مرفق** button, which uploads through the same `frappe.ui.FileUploader` widget the
  sidebar used and appends a row defaulting to type `Attachment`.

Either way the result is one row in one table.

## The rules the table enforces

* `attachment_type` is a controlled vocabulary - `Main Letter`, `Attachment`, `Reply` - and
  defaults to `Attachment`.
* `folder` is **optional**. It used to be required free text, which produced values like
  "نن" typed by someone who had to put something there. An empty folder is honest; an
  invented one is not.
* The same file cannot be recorded twice under the same type
  (`services/records.py::validate_attachment_rows`, called from both controllers).
* `file_hash` is read-only and written automatically.
* A sealed record refuses new or changed attachments, and the upload button is withheld with
  an indicator explaining why.

## Still open

* `folder` is free text. Making it a controlled list would be better, but it needs the
  archive's actual location names and a migration for existing values.
* `is_secret` hides a file's **name** in the panel and the print format. It does not restrict
  access to the `File` document itself - that is governed by Frappe's own File permissions.
