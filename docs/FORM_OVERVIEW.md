# Form overview panels

What a user sees the moment a correspondence or a referral is opened.

Two panels, one on each form: everything recorded against the document, in one place,
without a click.

| Panel | Field | On DocType | Rendered by |
|---|---|---|---|
| النظرة الشاملة على المعاملة | `overview_html` | Murasalat Correspondence | `services/overview.py` → `templates/overview/correspondence.html` |
| النظرة الشاملة على الإحالة | `overview_html` | Murasalat Referral | `services/overview.py` → `templates/overview/referral.html` |

`overview_html` is the **first field in `field_order`** on both forms, so the panel is what
you see the moment the document opens.

---

## Why it is built this way

Four decisions, each taken to keep the Native‑First principle intact while still being
worth looking at:

1. **Server-rendered, not hand-built in the browser.** The markup is produced by Jinja
   templates in `templates/overview/`. That makes the panel *testable* — the test suite
   renders both templates and asserts on the output — and keeps the client script to
   about forty lines of connector.
2. **HTML fields, not a custom page.** Frappe's `HTML` field type is the native way to
   place server-rendered content on a form.
3. **`frm.dashboard.add_indicator(...)` for the status chips.** This is Frappe's own
   dashboard API (verified against `frappe/public/js/frappe/form/dashboard.js`), so the
   indicators match Desk's own styling and appear in the standard dashboard area.
4. **Native Connections stay in place.** The panels are *presentation*; the Connections
   tab (`internal_links` / `get_data()`) remains the native mechanism for linked
   documents, and each panel row is a plain link to the record.

**Nothing here decides access.** Every query goes through
`frappe.get_list(..., ignore_permissions=False)` and every anchor document through
`doc.check_permission("read")`. There is no `ignore_permissions=True` anywhere in
`services/overview.py`, no `frappe.db.sql`, and no second authorization model. The test
suite fails if any of those change.

---

## What the correspondence panel shows

- **Header**: subject, document number, concerned person, current holder, plus chips for
  workflow state, direction, confidentiality, importance, transaction type, `مختومة`, `مغلقة`.
- **KPI row**: open referrals, overdue, due today, completed, drafts, total referrals,
  attachments (with the secret count).
- **Referrals table**: number (a link to the referral), recipient with its type,
  a state chip that distinguishes *completed* from *overdue* from *due today* from *open*
  from *draft*, due date with days remaining, the three lifecycle stamps, and the
  private / follow-up / paper-copy / cc markers.
- **Linked records** from the `links` child table.
- **Official data**: internal and external numbers, external letter date, due date with
  days remaining, page count, registration, closure, and any reopen.
- **Approval requests**: level, state, requester, and the decision or a *بانتظار القرار* chip.
- **Recent movements**: a timeline of the activity trail, newest first.
- **Seal and integrity**: seal date and user, seal reason, and the SHA‑256 hash — or an
  explanation of what sealing will do while the record is still open.

## What the referral panel shows

- **Header**: referral number, recipient with its type, the parent file, and chips for
  state, draft / overdue / remaining days / completed / private / importance / direction /
  follow-up.
- **Lifecycle stamps**: sent, received (with who), completed (with who), and the due date
  with its countdown. A stamp not yet reached is shown dashed and stated plainly
  (*لم تُستلم*) rather than left blank.
- **Instructions to the recipient.**
- **Parent correspondence card**: number, subject, direction, state, current holder,
  confidentiality — and its sealed state if it is sealed.
- **The file's other referrals**, so the user sees the whole work context at a glance.
- **This referral's own trail**: the activity rows recorded against it on the parent.
- **Approval requests** on the parent file.

### When the user cannot read the parent

A referral is a separate document: a user may be able to open it and not the file it
belongs to. In that case the parent card prints *مقيّد — لا تملك صلاحية قراءة المعاملة
المرتبطة* and the sibling list says the same, instead of leaking a subject or a list of
co-workers' tasks. This mirrors the `[Restricted]` discipline the reports already follow.

---

## Security note

Both templates are rendered with `autoescape=select_autoescape(["html"])`. Anything a user
typed — a subject, a body, an instruction block, a remarks field — is escaped, so the panel
cannot become a script-injection surface. The tests assert this with real payloads
(`<script>`, `<img onerror=…>`).

Links inside the panel use Desk's standard route form
(`/app/murasalat-referral/<name>`), so a click opens the record in the normal viewer and
the destination applies its own permissions.

---

## Verification

```bash
python -m pytest murasalat_office/tests/test_form_overview.py -q
```

The suite covers the counters (including that a completed-but-late referral is *done*, not
overdue, and that datetime strings and missing due dates do not break the arithmetic),
renders both templates, asserts escaping, asserts the restricted-parent path, asserts the
empty-record path, asserts that every `frappe.get_list` stays permission-aware, and pins
the layout (the field exists, is of type HTML, and comes first).

What it cannot cover without a Bench — that Desk fetches and injects the panel — is
covered by source contract on the two client scripts, and by `node --check` on their syntax.

---

## Customising

- **Content**: edit the template. The context is assembled in `services/overview.py`;
  adding a field means adding it to the context dict.
- **Look**: each template carries its own scoped `<style>` block under the `.mo-ov`
  prefix, so nothing leaks into Desk's own styling and no asset needs loading.
- **Adding a section to another DocType**: add a context builder and a template, then call
  `render(name, **context)` from a whitelisted endpoint. Do not add rendering logic to
  the client script.
