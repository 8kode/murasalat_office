"""Attach access roles to the operational reports, after migrate.

The report definitions deliberately ship without roles. A Report's roles are Link fields to
Role documents, and ``bench migrate`` syncs a report's JSON **before** the correspondence
roles exist on a fresh site, so a role named in the JSON can fail the sync. Running this
after migrate avoids that ordering trap while still making report access explicit.

    bench --site <site> execute murasalat_office.setup.report_access.apply_report_roles

It is idempotent: roles already attached are left alone.

**Why this writes child rows directly instead of appending to the Report:** saving a Report
document writes its definition back out to the app tree. Doing that from a setup script
silently edits tracked source files as a side effect of configuring a site — which is
exactly what happened the first time this ran. The roles now go straight into the ``Has
Role`` table, so configuring a site no longer modifies the repository.
"""
import json
import os

CORRESPONDENCE_ROLES = (
    "Correspondence Clerk",
    "Correspondence Supervisor",
    "Correspondence Auditor",
)

ALWAYS = ("System Manager",)


def report_dir():
    """The report folder inside the app, resolved without importing frappe."""
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(os.path.dirname(here), "murasalat_office", "report")


def report_slugs():
    """Every shipped report, read from the app tree."""
    base = report_dir()

    if not os.path.isdir(base):
        return []

    return sorted(
        folder
        for folder in os.listdir(base)
        if os.path.isdir(os.path.join(base, folder)) and folder != "__pycache__"
    )


def report_names():
    """The Report document name for each shipped report, read from its own definition.

    Resolved from disk rather than guessed with a ``like`` filter: a guess matches the
    wrong document when one report name contains another.
    """
    base = report_dir()
    names = []

    for slug in report_slugs():
        meta_path = os.path.join(base, slug, f"{slug}.json")

        if not os.path.isfile(meta_path):
            continue

        with open(meta_path) as handle:
            definition = json.load(handle)

        name = definition.get("report_name") or definition.get("name")

        if name:
            names.append((slug, name))

    return names


def desired_roles():
    return tuple(sorted(set(ALWAYS) | set(CORRESPONDENCE_ROLES)))


def apply_report_roles():
    import frappe

    created = []

    for role in CORRESPONDENCE_ROLES:
        if not frappe.db.exists("Role", role):
            frappe.get_doc(
                {"doctype": "Role", "role_name": role, "desk_access": 1}
            ).insert(ignore_permissions=True)
            created.append(role)

    wanted = desired_roles()
    changed = []

    for slug, name in report_names():
        if not frappe.db.exists("Report", name):
            print(f"  skip  {slug}: no Report document (run bench migrate first)")
            continue

        attached = {
            row.role
            for row in frappe.get_all(
                "Has Role",
                filters={"parent": name, "parenttype": "Report", "parentfield": "roles"},
                fields=["role"],
                limit_page_length=0,
            )
        }
        missing = [role for role in wanted if role not in attached]

        if not missing:
            print(f"  ok    {name}")
            continue

        for role in missing:
            # A direct child insert, so the Report definition on disk is left untouched.
            frappe.get_doc(
                {
                    "doctype": "Has Role",
                    "parent": name,
                    "parenttype": "Report",
                    "parentfield": "roles",
                    "role": role,
                }
            ).insert(ignore_permissions=True)

        changed.append(name)
        print(f"  set   {name} <- {', '.join(missing)}")

    if created:
        print(f"created roles: {', '.join(created)}")

    # bench execute does not commit on its own; without this the roles are rolled back
    # when the command returns.
    frappe.db.commit()

    print(f"{len(changed)} report(s) updated")
    return changed
