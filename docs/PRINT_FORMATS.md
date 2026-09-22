# Print formats

Two standard print formats ship with the application, both native Frappe `Print Format`
documents packed inside the module folder:

| Format name | On DocType | Folder |
|---|---|---|
| `Murasalat Correspondence Print` | Murasalat Correspondence | `murasalat_office/print_format/murasalat_correspondence_print/` |
| `Murasalat Referral Notification` | Murasalat Referral | `murasalat_office/print_format/murasalat_referral_notification/` |

Each folder holds `<name>.html` (the Jinja template) and `<name>.json` (the Print Format
row). The template is embedded in the JSON as well, so the format still prints if a site
reads only the row; a test keeps the two in step.

They are **presentation, not governance** — no role, permission row, workflow or fixture
is introduced by shipping them. That distinction is what keeps the Native‑First promise
intact while a Desk-native document type is used for its intended purpose.

Both appear automatically in the **Print** menu of their DocType after
`bench --site <site> migrate`.

---

## Murasalat Correspondence Print

The official record of a correspondence. Bordered header with the document number, then:

- **Badges** for confidentiality, importance, transaction type, workflow state, and a
  red **مختومة** marker once the record is sealed.
- **Parties** resolved from the direction, mirroring `register_correspondence`:
  incoming → sender / receiving department, outgoing → sending department / external
  recipient, internal → from department / to department.
- **Metadata**: subject, internal number, registration date, external letter number and
  date, due date, page count, current holder, concerned person.
- **Body** (`notes`).
- **Attachments** with type, file name and a secret marker. A secret attachment prints as
  *مرفق سرّي — يُطلب من الأرشيف* rather than exposing its file path.
- **Signature row**: editor, recipient, official seal.
- **Integrity block**, printed only when the record is sealed: seal date and user, seal
  reason, reopen event, and the full SHA‑256 integrity hash.
- **Activity trail**: date, event, actor and detail, with the stored English activity
  values mapped to Arabic.

## Murasalat Referral Notification

The slip handed to the recipient, with a tear-off return strip.

- **Directed-to box** showing whether the referral went to a user or a department.
- **Badges**: a dark **خاص** banner for private referrals, a red overdue / due-today
  marker computed against the due date, importance, follow-up, paper-copy and cc markers.
- **Metadata**: referral number, parent correspondence, due date, sent / received /
  completed stamps with their actors.
- **Instructions** to the recipient, in a bordered block for handwriting.
- **Parent correspondence body** for context — read through
  `frappe.has_permission("Murasalat Correspondence", doc=…, ptype="read")`. A user without
  access to the file sees *مقيّد — لا تملك صلاحية قراءة هذه المعاملة* instead of its
  content, the same discipline the permission-aware reports follow.
- **Signature row** and a **cut line** instructing the recipient to return the signed
  strip to the correspondence office.

---

## Customising

Edit the `.html` file, keep the `.json` in step (or delete the JSON's `html` value and let
the file be the only source), then migrate. For a site-specific variant that must not be
overwritten on upgrade, create a **new** Print Format from Desk instead of editing the
standard one.

Both templates are Arabic-only by design: labels are written in Arabic rather than wrapped
in `_()`, so a printed document never depends on `ar.csv` being complete. An English site
can add a translated Print Format from Desk.

## Verification

```bash
python -m pytest murasalat_office/tests/test_print_formats.py -q
```

The suite parses both templates with Jinja (a syntax error would otherwise surface only
when somebody tries to print), and checks every `doc.<field>` and every child-table loop
variable against the DocType metadata — a mistyped field name prints an empty cell, which
this catches before it reaches paper.
