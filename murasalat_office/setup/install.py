"""Make a fresh site usable, from the install command, without shipping fixtures.

Frappe runs ``after_install`` (a list of dotted paths - ``frappe/installer.py``) at the end of
``bench --site <site> install-app``, after DocTypes, Workspaces, sidebars and Dashboards are
synced, so everything the provisioners reference already exists at that point. It runs
``after_migrate`` (``frappe/migrate.py``) on every ``bench migrate``.

That trigger is what this module supplies. Before it, ``install-app`` + ``migrate`` left a site
with the DocTypes and the Desk furniture but no roles, no permission rows, no Workflows, no
master data and no report roles: the first user saw an empty application and a readiness report
full of missing items, and had to run ``provision.apply`` by hand to get anything.

Nothing here is destructive. ``setup.provision`` creates what is missing and reports what it
found - an existing Workflow, possibly edited in Desk, is never overwritten - and the same
holds for ``setup.master_data``, ``setup.report_print_formats``, ``setup.notifications`` and
``setup.report_access``. Running the whole routine on an already-provisioned site changes
nothing and returns a report.

A failure here must not abort ``install-app`` or ``bench migrate``: a half-installed app is
worse than an installed one that still needs provisioning. Every step is attempted, the failure
is written to Error Log, and the console gets the exact command to run by hand.
"""
import frappe


def install():
    """``after_install``: create the launch configuration, then report readiness."""
    return _provision(verbose=True)


def top_up():
    """``after_migrate``: create whatever a newer version added, and nothing else."""
    return _provision(verbose=False)


def _provision(verbose):
    report = {"created": {}, "errors": []}

    for step, runner in _steps():
        try:
            report["created"][step] = runner()
        except Exception as exc:  # noqa: BLE001 - reported, never raised: see module docstring
            report["errors"].append(f"{step}: {exc}")
            frappe.log_error(
                title=f"Murasalat Office provisioning failed at {step}",
                message=frappe.get_traceback(),
            )

    _announce(report, verbose=verbose)
    return report


def _steps():
    """The provisioners, in the order they must run.

    ``provision.apply`` already covers master data, the roles and their permission rows, the
    Workflows with a task attached to every transition, the report print formats and the
    notifications. Report visibility on top of that is ``report_access``'s job.
    """
    from murasalat_office.setup import provision, report_access

    return (
        ("provision", lambda: provision.apply(confirm=True)),
        ("report_roles", report_access.apply_report_roles),
    )


def _announce(report, verbose):
    if not report["errors"] and not verbose:
        print("Murasalat Office: provisioning checked, nothing missing.")
        return

    lines = ["", "Murasalat Office provisioning", "=" * 31]
    for step in report["created"]:
        lines.append(f"  ok    {step}")

    for error in report["errors"]:
        lines.append(f"  FAIL  {error}")

    if report["errors"]:
        lines += [
            "",
            "  The site is not launchable yet. Re-run the provisioner by hand:",
            "    bench --site <site> execute murasalat_office.setup.provision.apply \\",
            "        --kwargs \"{'confirm': True}\"",
            "  Then read what is still missing:",
            "    bench --site <site> execute murasalat_office.setup.provision.readiness",
        ]
    else:
        lines += ["", "  Readiness", "  " + "-" * 29]
        print("\n".join(lines))
        try:
            _readiness()
        except Exception as exc:  # noqa: BLE001 - the report already carried the work
            report["errors"].append(f"readiness: {exc}")
            print(f"  FAIL  readiness: {exc}")
        return

    print("\n".join(lines))


def _readiness():
    from murasalat_office.setup import provision

    provision.readiness()
