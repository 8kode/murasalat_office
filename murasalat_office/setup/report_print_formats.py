"""Create the A4 print formats for the three management reports.

Why this exists instead of being picked up by `bench migrate` like the two DocType print
formats: Frappe's ``PrintFormat.before_save`` forces every report format to
``custom_format = 1`` and ``standard = "No"`` -

    def before_save(self):
        if self.print_format_for == "Report":
            self.custom_format = 1
            self.standard = "No"

- because the framework treats a report layout as a site customisation rather than a document an
application ships. A row that is not ``standard = "Yes"`` is not re-imported from the module
folder, so the formats are created here through Frappe's own model instead - exactly what Desk
does when somebody saves a Print Format by hand, which keeps the Native-First promise intact.

The template itself lives in ``print_format/<slug>/<slug>.html`` and is read from there, so the
shipped file stays the single source. An existing format is reported, never overwritten: a site
may have restyled it.

    bench --site <site> execute murasalat_office.setup.report_print_formats.plan
    bench --site <site> execute murasalat_office.setup.report_print_formats.install
"""
import json
import pathlib

import frappe

MODULE = "Murasalat Office"

# slug -> the Report the format prints
FORMATS = {
    "murasalat_management_summary_print": "Murasalat Management Summary",
    "murasalat_department_workload_print": "Murasalat Department Workload",
    "murasalat_response_times_print": "Murasalat Response Times",
}


def _folder(slug):
    return pathlib.Path(frappe.get_app_path("murasalat_office", MODULE.lower().replace(" ", "_"),
                                            "print_format", slug))


def _definition(slug):
    """Read what the app ships: the JSON for metadata, the HTML for the template."""
    folder = _folder(slug)
    meta = json.loads((folder / f"{slug}.json").read_text(encoding="utf-8"))
    meta["html"] = (folder / f"{slug}.html").read_text(encoding="utf-8")
    return meta


def plan():
    """Read-only: which formats are missing, which already exist, and on which report."""
    return [
        {
            "format": slug,
            "report": report,
            "exists": bool(frappe.db.exists("Print Format", _definition(slug)["name"])),
        }
        for slug, report in FORMATS.items()
    ]


def install():
    """Create the missing formats. Idempotent, and never overwrites an existing one."""
    report = {"created": [], "exists": [], "errors": []}

    for slug, report_name in FORMATS.items():
        try:
            definition = _definition(slug)
        except Exception as exc:  # noqa: BLE001 - a missing file is reported, not thrown
            report["errors"].append(f"{slug}: {exc}")
            continue

        if frappe.db.exists("Print Format", definition["name"]):
            report["exists"].append(definition["name"])
            continue

        try:
            frappe.get_doc(definition).insert(ignore_permissions=True)
        except Exception as exc:  # noqa: BLE001
            report["errors"].append(f"{definition['name']}: {exc}")
            continue

        report["created"].append(definition["name"])

    return report
