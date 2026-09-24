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

The template lives with its report, at ``report/<report_slug>/<report_slug>.html``, and is read
from there. That file is also what the framework itself loads for a report:
``frappe.desk.query_report.get_script`` reads ``<module>/report/<report>/<report>.html`` and hands
its text to the browser as the report's own default print template. So one file drives both
routes - a site that never runs this installer still prints the A4 layout, because the browser
picks the report's template up by itself.

Two things are copied into the Print Format row from that file:

* ``html`` - the template itself, so the dialog's Print Format list has something to render;
* ``print_format_type = "JS"`` - the report print dialog only offers formats whose type is JS,
  because a report layout is rendered in the browser and never on the server.

Installation is idempotent. A row that is already there is not re-created; if the template it
holds differs from the shipped file it is brought up to date, so a corrected layout actually
reaches a site where the format was installed earlier.

    bench --site <site> execute murasalat_office.setup.report_print_formats.plan
    bench --site <site> execute murasalat_office.setup.report_print_formats.install
"""
import json
import pathlib

import frappe

MODULE = "Murasalat Office"

# format slug -> the Print Format it installs and the Report it prints
FORMATS = {
    "murasalat_management_summary_print": {
        "name": "Murasalat Management Summary Print",
        "report": "Murasalat Management Summary",
        "report_slug": "murasalat_management_summary",
    },
    "murasalat_department_workload_print": {
        "name": "Murasalat Department Workload Print",
        "report": "Murasalat Department Workload",
        "report_slug": "murasalat_department_workload",
    },
    "murasalat_response_times_print": {
        "name": "Murasalat Response Times Print",
        "report": "Murasalat Response Times",
        "report_slug": "murasalat_response_times",
    },
}


def _module_path(*joins):
    return pathlib.Path(
        frappe.get_app_path("murasalat_office", MODULE.lower().replace(" ", "_"), *joins)
    )


def template_path(report_slug):
    """The one file that holds the layout: shipped with the report, read by the framework too."""
    return _module_path("report", report_slug, f"{report_slug}.html")


def template(report_slug):
    return template_path(report_slug).read_text(encoding="utf-8")


def _definition(slug):
    """The metadata the app ships, plus the template read from its single source."""
    spec = FORMATS[slug]
    folder = _module_path("print_format", slug)
    meta = json.loads((folder / f"{slug}.json").read_text(encoding="utf-8"))
    meta["html"] = template(spec["report_slug"])
    meta["print_format_type"] = "JS"
    meta["report"] = spec["report"]
    return meta


def plan():
    """Read-only: which formats exist, which are out of date, and on which report."""
    rows = []
    for slug, spec in FORMATS.items():
        name = spec["name"]
        exists = bool(frappe.db.exists("Print Format", name))
        rows.append(
            {
                "format": name,
                "report": spec["report"],
                "exists": exists,
                "current": exists and frappe.db.get_value("Print Format", name, "html")
                == template(spec["report_slug"]),
            }
        )
    return rows


def install():
    """Create the missing formats and refresh an out-of-date template. Idempotent."""
    result = {"created": [], "exists": [], "updated": [], "errors": []}

    for slug, spec in FORMATS.items():
        name = spec["name"]
        try:
            definition = _definition(slug)
        except Exception as exc:  # noqa: BLE001 - a missing file is reported, not thrown
            result["errors"].append(f"{name}: {exc}")
            continue

        if frappe.db.exists("Print Format", name):
            if frappe.db.get_value("Print Format", name, "html") == definition["html"]:
                result["exists"].append(name)
                continue
            try:
                frappe.db.set_value(
                    "Print Format",
                    name,
                    {"html": definition["html"], "print_format_type": "JS"},
                )
            except Exception as exc:  # noqa: BLE001
                result["errors"].append(f"{name}: {exc}")
                continue
            result["updated"].append(name)
            continue

        try:
            frappe.get_doc(definition).insert(ignore_permissions=True)
        except Exception as exc:  # noqa: BLE001
            result["errors"].append(f"{name}: {exc}")
            continue

        result["created"].append(name)

    return result
