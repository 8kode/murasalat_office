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
- **Attachments** with the type printed in Arabic rather than its stored Select value
  (`Main Letter` -> *الخطاب الأصلي*), the file name, and a secret marker. A secret
  attachment prints as
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
- **Attachments** carried by the referral, in the same table the correspondence record
  prints - number, type in Arabic, file name, secret marker - with a count of the
  attachments withheld and a line telling the recipient to request them from the archive.
  The slip is the paper that travels with the file, so it now states what is travelling.
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

The suite also **renders** both templates against a stubbed `frappe` and a record carrying
one ordinary and one secret attachment: a Jinja slip that would otherwise surface only on
somebody's print is caught here, and the secret file name is asserted absent from the
output so a redaction regression cannot ship silently.

---

## Report layouts — the three management reports

`Murasalat Management Summary`, `Murasalat Department Workload` and `Murasalat Response Times`
print an A4 layout instead of the framework's plain grid. Three facts about how Frappe prints a
report decide how that layout is shipped, and all three had to be answered before a printed
report looked like the screen:

1. **A report prints through its own template, or through the grid.** `query_report.js`:

   ```js
   get_print_template(print_settings, custom_format) {
       return print_settings.columns?.length || !custom_format ? "print_grid" : custom_format;
   }
   ```

   With no template of its own, every report prints `print_grid` — the framework's default grid.
   That, and nothing else, is why a report appears to ignore a Print Format.
2. **The template Frappe looks for is a file next to the report.**
   `frappe.desk.query_report.get_script` reads `<module>/report/<report>/<report>.html` and returns
   its text as `html_format`, which `get_custom_format` starts from. Shipping that file is the
   whole fix: **Print** and **PDF** then use the A4 layout with no dialog step at all.
3. **A report layout is rendered in the browser, not on the server.** It goes through
   `frappe/public/js/frappe/microtemplate.js`, whose grammar is a small JavaScript templating
   language — not Jinja. `{% set %}`, `{% elif %}`, `| length`, `| safe`, the `in` operator,
   `loop.index0` and `or` all compile to invalid JavaScript and the report prints **nothing**;
   `{% if list %}` is true for an empty list here, because an empty array is truthy in
   JavaScript. Jinja accepts every one of those, so a Jinja check on a report layout passes while
   the browser fails.

### What each report ships

| Report | Layout file |
|---|---|
| `Murasalat Management Summary` | `murasalat_office/report/murasalat_management_summary/murasalat_management_summary.html` |
| `Murasalat Department Workload` | `murasalat_office/report/murasalat_department_workload/murasalat_department_workload.html` |
| `Murasalat Response Times` | `murasalat_office/report/murasalat_response_times/murasalat_response_times.html` |

The three files are byte-identical — one layout for all three reports — and a test fails if they
drift apart. Each layout carries a coloured title band, the filter strip the framework builds, a
dark teal table head with the total row highlighted, zebra striping done in CSS, and a footer
stating that the report was computed under the printing user's permissions.

### The same layout as a Print Format row

Alongside the file, `setup/report_print_formats.py` creates one `Print Format` row per report
(`Murasalat Management Summary Print`, …) so the layout can also be chosen explicitly in the print
dialog. Two framework details shape those rows:

- a report format is always `custom_format = 1` and `standard = "No"` — `PrintFormat.before_save`
  forces it, because the framework treats a report layout as site customisation — so
  `bench migrate` never imports them, and the installer creates them through Frappe's own model;
- the print dialog lists only formats with `print_format_type = "JS"` (its `get_query` filters on
  exactly that), which is what the rows now declare. A browser-rendered report layout *is* a JS
  format; declaring Jinja hides it from the dialog.

The template is embedded into the row from the layout file — the JSON keeps no second copy. A row
whose template has gone stale is refreshed on the next install, so a corrected layout actually
reaches a site that installed the format earlier.

```bash
bench --site <site> execute murasalat_office.setup.report_print_formats.plan     # read-only
bench --site <site> execute murasalat_office.setup.report_print_formats.install
```

### If a report still prints the plain grid

1. `…report_print_formats.plan` — does the report name match, and is the row current?
2. In the print dialog leave **Print Format** empty: the report's own template is used then.
   Picking a format switches to that format instead.
3. Leave **Pick Columns** unticked. Ticking it sets `print_settings.columns`, and
   `get_print_template` then returns the grid by design.
4. Arabic column headers and KPI labels come from `translations/ar.csv`; an English label on an
   Arabic report means its row is missing there.

### Verification

```bash
python -m pytest murasalat_office/tests/test_report_print_formats.py -q
```

Two layers: the metadata and the layout are checked as text — including a lint that rejects every
construct microtemplate cannot run — and the layout is **executed** in Frappe's own browser engine
by `tests/render_report_template.mjs`. That runner needs `node`, and locates
`…/apps/frappe/public/js/frappe/microtemplate.js` through `frappe.get_app_path`, a bench under the
home directory, or the `FRAPPE_MICROTEMPLATE` environment variable; it skips with that instruction
when neither can be found.
