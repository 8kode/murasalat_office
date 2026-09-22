"""Attach access roles to the operational reports, after migrate.

The report definitions deliberately ship without roles. A Report's roles are Link fields
to Role documents, and ``bench migrate`` syncs the JSON **before** the correspondence roles
exist on a fresh site, so a role named in the JSON can fail the sync. Running this after
migrate avoids that ordering trap while still making report access explicit rather than
implicit.

    bench --site <site> execute murasalat_office.setup.report_access.apply_report_roles

It is idempotent: roles that are already attached are left alone.
"""
from pathlib import Path

CORRESPONDENCE_ROLES = (
    "Correspondence Clerk",
    "Correspondence Supervisor",
    "Correspondence Auditor",
)

ALWAYS = ("System Manager",)


def report_slugs():
    """Every shipped report, read from the app tree.

    Kept free of ``frappe`` on purpose so it can be asserted without a bench.
    """
    root = Path(__file__).resolve().parents[1] / "murasalat_office/report"
    if not root.is_dir():
        return []
    return sorted(
        folder.name
        for folder in root.iterdir()
        if folder.is_dir() and folder.name != "__pycache__"
    )


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

    changed = []
    wanted = desired_roles()

    for slug in report_slugs():
        name = frappe.db.get_value("Report", {"name": ("like", f"%{slug}%")}, "name")
        if not name:
            print(f"  skip  {slug}: no Report document (run bench migrate first)")
            continue

        report = frappe.get_doc("Report", name)
        attached = {row.role for row in report.roles}
        missing = [role for role in wanted if role not in attached]

        if not missing:
            print(f"  ok    {name}")
            continue

        for role in missing:
            report.append("roles", {"role": role})

        report.save(ignore_permissions=True)
        changed.append(name)
        print(f"  set   {name} <- {', '.join(missing)}")

    if created:
        print(f"created roles: {', '.join(created)}")
    print(f"{len(changed)} report(s) updated")
    return changed
