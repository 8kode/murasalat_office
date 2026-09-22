"""Configuration checks that need a running site.

The framework-light suite cannot see a migrated database, so a handful of things can only
be confirmed on a bench:

    bench --site <site> execute murasalat_office.verification.site_smoke.run

Every check is read-only. Each line prints PASS, WARN or FAIL. A WARN is something that is
not wrong but leaves a capability unused; a FAIL is something that will not work.

Two things this script learned the hard way, both kept as comments where they bite:

* Report names must be resolved from the report definition on disk, not guessed by a
  ``like`` filter. ``%queue%`` matches Work Queue *and* Follow Up Queue, so a guess
  reports the wrong document and can report the same one several times.
* A ``workflow_methods`` hook only fires through a transition task, and **only on the
  Frappe versions that implement transition tasks at all**. The script checks for that
  support rather than reporting a failure the site cannot fix.
"""
import json
import os

import frappe

CORRESPONDENCE = "Murasalat Correspondence"
REFERRAL = "Murasalat Referral"

STATUS = {"pass": 0, "warn": 0, "fail": 0}


def _pass(label, detail=""):
    STATUS["pass"] += 1
    print(f"  PASS  {label}" + (f"  [{detail}]" if detail else ""))


def _warn(label, detail=""):
    STATUS["warn"] += 1
    print(f"  WARN  {label}" + (f"  [{detail}]" if detail else ""))


def _fail(label, detail=""):
    STATUS["fail"] += 1
    print(f"  FAIL  {label}" + (f"  [{detail}]" if detail else ""))


def _report_dir():
    return frappe.get_app_path("murasalat_office", "murasalat_office", "report")


def _shipped_reports():
    """Yield (slug, report_name) for every report definition on disk."""
    base = _report_dir()

    for slug in sorted(os.listdir(base)):
        meta_path = os.path.join(base, slug, f"{slug}.json")

        if not os.path.isfile(meta_path):
            continue

        with open(meta_path) as handle:
            definition = json.load(handle)

        yield slug, definition.get("report_name") or definition.get("name")


def _hook_map():
    """The app's workflow_methods, keyed by the name a transition task refers to."""
    entries = frappe.get_hooks("workflow_methods") or []
    return {entry.get("name"): entry.get("method") for entry in entries if entry.get("name")}


def _workflow_transitions(workflow_name):
    return frappe.get_all(
        "Workflow Transition",
        filters={"parent": workflow_name},
        fields=["name", "action", "state", "next_state"],
        order_by="idx",
        limit_page_length=0,
    )


def _check_doctypes():
    print("doctypes")

    for doctype in (
        CORRESPONDENCE,
        "Murasalat Referral",
        "Murasalat Approval Request",
        "Murasalat Correspondence Activity",
        "Murasalat Correspondence Link",
        "Murasalat Attachment",
        "Murasalat User Organization Membership",
    ):
        if frappe.db.exists("DocType", doctype):
            _pass(doctype)
        else:
            _fail(doctype, "not migrated")


def _transition_task_field():
    """The Link field on Workflow Transition that points at a transition-task group.

    Returns None on Frappe versions that do not implement transition tasks, in which case
    no transition can run a workflow_methods hook no matter how the site is configured.
    """
    meta = frappe.get_meta("Workflow Transition")
    return "transition_tasks" if meta.has_field("transition_tasks") else None


def _check_workflow():
    print("workflow")

    field = _transition_task_field()
    hooks = _hook_map()

    if not field:
        _warn(
            "transition tasks are not implemented by this Frappe version",
            "a workflow_methods hook cannot be attached to a transition here; "
            "the lifecycle methods have to be called another way",
        )

    for doctype in (CORRESPONDENCE, REFERRAL):
        workflows = frappe.get_all(
            "Workflow",
            filters={"document_type": doctype, "is_active": 1},
            fields=["name"],
            limit_page_length=0,
        )

        if not workflows:
            _fail(f"{doctype}: active workflow", "no is_active Workflow for this DocType")
            continue

        for workflow in workflows:
            transitions = _workflow_transitions(workflow.name)
            _pass(f"{doctype}: workflow {workflow.name}", f"{len(transitions)} transitions")

            for transition in transitions:
                action = transition.action
                expected = hooks.get(action)

                if not field:
                    continue

                group = frappe.db.get_value(
                    "Workflow Transition", transition.name, field
                ) if frappe.db.has_column("Workflow Transition", field) else None

                rows = []
                if group:
                    rows = frappe.get_all(
                        "Workflow Transition Task",
                        filters={"parent": group, "enabled": 1},
                        fields=["task", "link", "asynchronous"],
                        order_by="idx",
                        limit_page_length=0,
                    )

                if not rows:
                    if expected:
                        _fail(
                            f"{action} ({transition.state} -> {transition.next_state})",
                            f"no transition task, so {expected.split('.')[-1]} never runs",
                        )
                    else:
                        _warn(
                            f"{action} ({transition.state} -> {transition.next_state})",
                            "no transition task; no hook of this name is registered",
                        )
                    continue

                for row in rows:
                    method = hooks.get(row.task)

                    if not method:
                        _fail(
                            f"{action}: task {row.task}",
                            "no workflow_methods entry with this name",
                        )
                    elif row.asynchronous:
                        _fail(
                            f"{action}: task {row.task}",
                            "'Asynchronous' is on, so the lifecycle method runs outside the "
                            "transition's transaction instead of inline",
                        )
                    else:
                        _pass(f"{action}: task {row.task}", method.split(".")[-1])

                if expected:
                    covered = {row.task for row in rows}
                    if expected != next((hooks.get(task) for task in covered), None):
                        _warn(
                            f"{action}: hook coverage",
                            f"expected {expected.split('.')[-1]} to be attached",
                        )


def _check_reports():
    print("reports")

    for slug, name in _shipped_reports():
        if not name:
            _fail(slug, "the report definition has no report_name")
            continue

        if not frappe.db.exists("Report", name):
            _fail(name, "Report document not found after migrate")
            continue

        roles = frappe.get_all(
            "Has Role",
            filters={"parent": name, "parenttype": "Report", "parentfield": "roles"},
            fields=["role"],
            order_by="idx",
            limit_page_length=0,
        )

        if not roles:
            _fail(
                name,
                "no roles attached, so report access is not explicitly governed "
                "(run murasalat_office.setup.report_access.apply_report_roles)",
            )
        else:
            _pass(name, ", ".join(sorted(row.role for row in roles)))


def _check_print_formats():
    print("print formats")

    for doctype in (CORRESPONDENCE, REFERRAL):
        names = frappe.get_all(
            "Print Format",
            filters={"doc_type": doctype},
            fields=["name"],
            limit_page_length=0,
        )

        if names:
            _pass(f"{doctype}: {', '.join(sorted(row.name for row in names))}")
        else:
            _fail(f"{doctype}: print format")


def _check_lifecycle_hooks():
    print("lifecycle hooks")

    import importlib

    for name, method in sorted(_hook_map().items()):
        try:
            module_path, function_name = method.rsplit(".", 1)
            getattr(importlib.import_module(module_path), function_name)
        except Exception as error:  # noqa: BLE001 - the message is the point
            _fail(f"{name}: {method}", str(error))
        else:
            _pass(f"{name}: {method}")


def _check_translations():
    """App translations come from the app's own CSV, not from the Translation doctype.

    Frappe loads ``{app}/translations/{lang}.csv`` on every request and layers the
    ``Translation`` doctype on top for user overrides. A site with a full Arabic CSV and
    zero Translation rows is translated correctly, so reporting that as a failure would
    send someone chasing a problem that does not exist.
    """
    print("translations")

    path = frappe.get_app_path("murasalat_office", "translations", "ar.csv")

    if not os.path.isfile(path):
        _fail("translations/ar.csv", "missing from the app")
    else:
        with open(path, encoding="utf-8") as handle:
            rows = [line for line in handle.read().splitlines() if line.strip()]

        if len(rows) < 2:
            _fail("translations/ar.csv", "no translation rows")
        else:
            _pass("translations/ar.csv", f"{len(rows) - 1} rows")

    if not frappe.db.exists("Language", "ar"):
        _fail("Language: ar", "not registered; the app cannot switch to Arabic")
        return

    if frappe.db.get_value("Language", "ar", "enabled"):
        _pass("Language: ar", "enabled")
    else:
        _fail("Language: ar", "registered but not enabled")


def run():
    print("Murasalat Office site verification")
    print("=" * 40)

    for check in (
        _check_doctypes,
        _check_workflow,
        _check_reports,
        _check_print_formats,
        _check_lifecycle_hooks,
        _check_translations,
    ):
        check()

    print("=" * 40)
    print(f"{STATUS['pass']} passed, {STATUS['warn']} warned, {STATUS['fail']} failed")
    print("Rendering still has to be eyeballed: see docs/VERIFICATION.md")

    return STATUS["fail"]
