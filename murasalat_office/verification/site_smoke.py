"""Configuration checks that need a running site.

The framework-light suite cannot see a migrated database, so a handful of things can only
be confirmed on a bench. Run them after ``bench migrate``:

    bench --site <site> execute murasalat_office.verification.site_smoke.run

Every check is read-only and reports a pass/fail line. This covers *configuration*; it does
not judge how anything looks. The rendering checklist lives in docs/VERIFICATION.md.
"""
import frappe


def _ok(label, detail=""):
    print(f"  PASS  {label}" + (f"  [{detail}]" if detail else ""))


def _fail(label, detail=""):
    print(f"  FAIL  {label}" + (f"  [{detail}]" if detail else ""))
    return 1


def _check_doctypes():
    failures = 0
    print("doctypes")

    for doctype in (
        "Murasalat Correspondence",
        "Murasalat Referral",
        "Murasalat Approval Request",
        "Murasalat Correspondence Activity",
        "Murasalat Correspondence Link",
        "Murasalat Attachment",
        "Murasalat User Organization Membership",
    ):
        if frappe.db.exists("DocType", doctype):
            _ok(doctype)
        else:
            failures += _fail(doctype, "not migrated")

    return failures


def _check_workflow():
    print("workflow")
    failures = 0

    for doctype in ("Murasalat Correspondence", "Murasalat Referral"):
        workflows = frappe.get_all(
            "Workflow",
            filters={"document_type": doctype, "is_active": 1},
            fields=["name"],
            limit_page_length=0,
        )
        if not workflows:
            failures += _fail(f"{doctype}: active workflow")
            continue

        for workflow in workflows:
            transitions = frappe.get_all(
                "Workflow Transition",
                filters={"parent": workflow.name},
                fields=["name", "action", "state", "next_state"],
                limit_page_length=0,
            )
            _ok(f"{doctype}: workflow {workflow.name}", f"{len(transitions)} transitions")

            tasks = frappe.get_all(
                "Workflow Transition Task",
                filters={"parenttype": "Workflow Transition", "parent": ("in", [t.name for t in transitions])},
                fields=["name", "enabled", "asynchronous", "task"],
                limit_page_length=0,
            )
            for task in tasks:
                if not task.enabled:
                    failures += _fail(f"transition task {task.name}", "not enabled")
                elif task.asynchronous:
                    failures += _fail(
                        f"transition task {task.name}",
                        "'Asynchronous' is on, so the lifecycle method will not run inline",
                    )
                else:
                    _ok(f"transition task {task.name}", task.task)

            if transitions and not tasks:
                failures += _fail(
                    f"{doctype}: transition tasks",
                    "no Workflow Transition Task rows, so no lifecycle method fires",
                )

    return failures


def _check_reports():
    print("reports")
    failures = 0

    report_dir = frappe.get_app_path("murasalat_office", "murasalat_office", "report")
    import os

    slugs = sorted(
        name
        for name in os.listdir(report_dir)
        if os.path.isdir(os.path.join(report_dir, name)) and name != "__pycache__"
    )

    for slug in slugs:
        name = frappe.db.get_value("Report", {"name": ("like", f"%{slug.split('_')[-1]}%")}, "name")
        if not name:
            failures += _fail(slug, "Report document not found after migrate")
            continue

        roles = frappe.get_all(
            "Has Role", filters={"parent": name, "parenttype": "Report"}, fields=["role"], limit_page_length=0
        )
        if not roles:
            failures += _fail(
                name,
                "no roles attached, so report access is not explicitly governed "
                "(run murasalat_office.setup.report_access.apply_report_roles)",
            )
        else:
            _ok(name, ", ".join(sorted(row.role for row in roles)))

    return failures


def _check_print_formats():
    print("print formats")
    failures = 0

    for doctype, expected in (
        ("Murasalat Correspondence", "Murasalat Correspondence Print"),
        ("Murasalat Referral", "Murasalat Referral Notification"),
    ):
        names = frappe.get_all(
            "Print Format", filters={"doc_type": doctype}, fields=["name"], limit_page_length=0
        )
        if not names:
            failures += _fail(f"{doctype}: print format")
        else:
            _ok(f"{doctype}: {expected}", ", ".join(sorted(row.name for row in names)))

    return failures


def _check_lifecycle_hooks():
    print("lifecycle hooks")
    failures = 0

    import importlib

    from murasalat_office import hooks

    for entry in getattr(hooks, "workflow_methods", []) or []:
        target = entry.get("method")
        try:
            module_path, function_name = target.rsplit(".", 1)
            getattr(importlib.import_module(module_path), function_name)
        except Exception as error:  # noqa: BLE001 - the message is the point
            failures += _fail(f"{entry.get('workflow_action') or '?'}: {target}", str(error))
        else:
            _ok(f"{entry.get('workflow_action') or '?'}: {target}")

    return failures


def _check_translations():
    print("translations")

    rows = frappe.get_all("Translation", filters={"language": "ar"}, limit_page_length=0)
    if not rows:
        return _fail("Arabic translations", "no Translation rows for 'ar'")

    _ok("Arabic translations", f"{len(rows)} rows")
    return 0


def run():
    print("Murasalat Office site verification")
    print("=" * 40)
    failures = 0

    for check in (
        _check_doctypes,
        _check_workflow,
        _check_reports,
        _check_print_formats,
        _check_lifecycle_hooks,
        _check_translations,
    ):
        failures += check()

    print("=" * 40)
    if failures:
        print(f"{failures} check(s) failed")
    else:
        print("all configuration checks passed")
    print("Rendering still has to be eyeballed: see docs/VERIFICATION.md")

    return failures
