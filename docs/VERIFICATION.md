# Verification: what is proven, and what only a running site can prove

The sandbox that authored these branches has no bench. Everything below is therefore split
into what the framework-light suite proves, what the site script proves on your bench, and
what a human still has to look at.

## 1. Proven without a bench

```bash
python -m pytest murasalat_office/tests -q      # the suite
python -m compileall -q murasalat_office        # every module byte-compiles
python murasalat_office/tests/validate_metadata.py   # metadata agrees with itself
node --check <every .js>
```

`.github/workflows/ci.yml` runs exactly these on every push and pull request, so a branch
cannot land with a broken report return, an unparsable JSON file, a report without its
client script, or a translation row that lost a column.

`validate_metadata.py` is also worth running locally before you commit metadata changes —
it is the check that catches the mistakes a metadata-only commit makes easy.

## 2. Proven on your bench, read-only

```bash
bench migrate
bench --site <site> execute murasalat_office.verification.site_smoke.run
```

It checks that the doctypes migrated, that each workflow has active transitions **and**
transition tasks with `Enabled` on and `Asynchronous` off (an asynchronous task silently
never fires the lifecycle method), that every report exists with roles attached, that the
print formats are present, that every lifecycle hook resolves to a real function, and that
Arabic translations loaded. Every line prints PASS or FAIL.

## 3. Still needs human eyes

These are the items no script here can settle:

| Item | Where to look |
| --- | --- |
| Chart and summary cards on the reports | Open each report; the summary must appear as cards, not as an empty chart |
| The `Reopen Reason` field and the `Unsealed` activity option | Open a sealed correspondence, reopen it, read the activity trail |
| The overview panel at the top of each form | Open a correspondence and a referral |
| Both print formats | Print preview on a real record — confirm Arabic renders and columns line up |
| List-view indicators | The correspondence list (sealed/closed) and the referral list (overdue/due today) |
| Report access after roles are applied | `bench --site <site> execute murasalat_office.setup.report_access.apply_report_roles`, then reopen a report as a non-System-Manager user |

Report the failures you see and they get fixed against a named symptom rather than a guess.
