import frappe
import json
import re


# ============================================================
# CONFIGURATION
# ============================================================

# False = Audit only, no deletion
# True  = Delete confirmed legacy metadata
APPLY_CHANGES = False

MODULE = "Murasalat Office"

# Known fields removed during the Murasalat refactor.
# Only these explicitly known legacy fields are eligible
# for automatic cleanup.
KNOWN_LEGACY_FIELDS = {
    "current_department",
    "uploaded_on",
    "documents_html",
    "referrals_html",
    "data_actions_html",
    "attachments_actions_html",
    "referrals_actions_html",
}


# ============================================================
# HELPERS
# ============================================================

def section(title):
    print("\n")
    print("=" * 100)
    print(title)
    print("=" * 100)


def safe_delete(doctype, name):
    """
    Delete through Frappe ORM.
    Never use direct SQL DELETE for metadata.
    """
    try:
        frappe.delete_doc(
            doctype,
            name,
            force=True,
            ignore_permissions=True,
        )

        print(f"  DELETE OK: {doctype} -> {name}")

        return True

    except Exception as e:
        print(f"  DELETE FAILED: {doctype} -> {name}")
        print(f"  ERROR: {e}")

        return False


def get_murasalat_doctypes():
    return frappe.get_all(
        "DocType",
        filters={
            "module": MODULE,
        },
        pluck="name",
    )


def get_valid_fields(doctype):
    try:
        meta = frappe.get_meta(doctype)

        return {
            df.fieldname
            for df in meta.fields
            if df.fieldname
        }

    except Exception:
        return set()


def contains_legacy_field(text):
    """
    Return all known legacy fields found in text.
    """
    if not text:
        return []

    found = []

    for field in KNOWN_LEGACY_FIELDS:
        if field in str(text):
            found.append(field)

    return sorted(found)


# ============================================================
# AUDIT
# ============================================================

section("MURASALAT LEGACY METADATA CLEANUP")
print(f"APPLY_CHANGES = {APPLY_CHANGES}")

murasalat_doctypes = get_murasalat_doctypes()

print("\nMurasalat DocTypes:")

for dt in murasalat_doctypes:
    print(f"  - {dt}")


report = {
    "client_scripts": [],
    "property_setters": [],
    "custom_fields": [],
    "server_scripts": [],
    "notifications": [],
    "print_formats": [],
    "reports": [],
    "invalid_workflows": [],
    "orphan_permission_levels": [],
    "deleted": [],
    "failed": [],
}


# ============================================================
# 1. CLIENT SCRIPTS
# ============================================================

section("1. CLIENT SCRIPT AUDIT")

client_scripts = frappe.get_all(
    "Client Script",
    filters={
        "dt": ["in", murasalat_doctypes],
    },
    fields=[
        "name",
        "dt",
        "enabled",
        "script",
    ],
)

for row in client_scripts:

    legacy_fields = contains_legacy_field(row.script)

    if legacy_fields:

        item = {
            "name": row.name,
            "doctype": row.dt,
            "enabled": row.enabled,
            "legacy_fields": legacy_fields,
        }

        report["client_scripts"].append(item)

        print("\nFOUND LEGACY CLIENT SCRIPT")
        print(f"  Name: {row.name}")
        print(f"  DocType: {row.dt}")
        print(f"  Fields: {legacy_fields}")

        if APPLY_CHANGES:

            # Automatic deletion only when the script references
            # known legacy fields.
            if safe_delete("Client Script", row.name):
                report["deleted"].append(
                    {
                        "doctype": "Client Script",
                        "name": row.name,
                    }
                )
            else:
                report["failed"].append(
                    {
                        "doctype": "Client Script",
                        "name": row.name,
                    }
                )


# ============================================================
# 2. PROPERTY SETTERS
# ============================================================

section("2. PROPERTY SETTER AUDIT")

property_setters = frappe.get_all(
    "Property Setter",
    fields=[
        "name",
        "doc_type",
        "field_name",
        "property",
        "value",
    ],
)

for row in property_setters:

    if row.doc_type not in murasalat_doctypes:
        continue

    valid_fields = get_valid_fields(row.doc_type)

    field_is_missing = (
        bool(row.field_name)
        and row.field_name not in valid_fields
    )

    referenced_legacy_fields = set()

    if row.field_name in KNOWN_LEGACY_FIELDS:
        referenced_legacy_fields.add(row.field_name)

    for field in contains_legacy_field(row.value):
        referenced_legacy_fields.add(field)

    if field_is_missing or referenced_legacy_fields:

        item = {
            "name": row.name,
            "doctype": row.doc_type,
            "field_name": row.field_name,
            "property": row.property,
            "value": row.value,
            "field_is_missing": field_is_missing,
            "legacy_fields": sorted(referenced_legacy_fields),
        }

        report["property_setters"].append(item)

        print("\nFOUND LEGACY PROPERTY SETTER")
        print(f"  Name: {row.name}")
        print(f"  DocType: {row.doc_type}")
        print(f"  Field: {row.field_name}")
        print(f"  Property: {row.property}")
        print(f"  Value: {row.value}")
        print(f"  Field Missing: {field_is_missing}")
        print(
            f"  Legacy Fields: "
            f"{sorted(referenced_legacy_fields)}"
        )

        # Safe automatic cleanup only when:
        # 1. The field no longer exists AND
        # 2. It is one of the explicitly known legacy fields.
        safe_to_delete = (
            field_is_missing
            and row.field_name in KNOWN_LEGACY_FIELDS
        )

        if APPLY_CHANGES and safe_to_delete:

            if safe_delete("Property Setter", row.name):
                report["deleted"].append(
                    {
                        "doctype": "Property Setter",
                        "name": row.name,
                    }
                )
            else:
                report["failed"].append(
                    {
                        "doctype": "Property Setter",
                        "name": row.name,
                    }
                )


# ============================================================
# 3. CUSTOM FIELDS
# ============================================================

section("3. CUSTOM FIELD AUDIT")

custom_fields = frappe.get_all(
    "Custom Field",
    filters={
        "dt": ["in", murasalat_doctypes],
    },
    fields=[
        "name",
        "dt",
        "fieldname",
        "label",
        "fieldtype",
        "permlevel",
    ],
)

for row in custom_fields:

    if row.fieldname in KNOWN_LEGACY_FIELDS:

        item = {
            "name": row.name,
            "doctype": row.dt,
            "fieldname": row.fieldname,
            "label": row.label,
            "fieldtype": row.fieldtype,
            "permlevel": row.permlevel,
        }

        report["custom_fields"].append(item)

        print("\nFOUND LEGACY CUSTOM FIELD")
        print(f"  Name: {row.name}")
        print(f"  DocType: {row.dt}")
        print(f"  Field: {row.fieldname}")
        print(f"  Type: {row.fieldtype}")

        # DO NOT auto-delete custom fields.
        # A Custom Field can contain real business data.
        print(
            "  ACTION: AUDIT ONLY "
            "(not automatically deleted)"
        )


# ============================================================
# 4. SERVER SCRIPTS
# ============================================================

section("4. SERVER SCRIPT AUDIT")

server_scripts = frappe.get_all(
    "Server Script",
    fields=[
        "name",
        "script_type",
        "reference_doctype",
        "script",
    ],
)

for row in server_scripts:

    if row.reference_doctype not in murasalat_doctypes:
        continue

    legacy_fields = contains_legacy_field(row.script)

    if legacy_fields:

        item = {
            "name": row.name,
            "script_type": row.script_type,
            "doctype": row.reference_doctype,
            "legacy_fields": legacy_fields,
        }

        report["server_scripts"].append(item)

        print("\nFOUND LEGACY SERVER SCRIPT")
        print(f"  Name: {row.name}")
        print(f"  Type: {row.script_type}")
        print(f"  DocType: {row.reference_doctype}")
        print(f"  Fields: {legacy_fields}")

        print(
            "  ACTION: AUDIT ONLY "
            "(not automatically deleted)"
        )


# ============================================================
# 5. WORKFLOW VALIDATION
# ============================================================

section("5. WORKFLOW AUDIT")

workflows = frappe.get_all(
    "Workflow",
    filters={
        "document_type": ["in", murasalat_doctypes],
    },
    fields=[
        "name",
        "document_type",
        "workflow_state_field",
        "is_active",
    ],
)

for row in workflows:

    valid_fields = get_valid_fields(row.document_type)

    if row.workflow_state_field not in valid_fields:

        item = {
            "name": row.name,
            "doctype": row.document_type,
            "workflow_state_field": row.workflow_state_field,
        }

        report["invalid_workflows"].append(item)

        print("\nINVALID WORKFLOW FIELD")
        print(f"  Workflow: {row.name}")
        print(f"  DocType: {row.document_type}")
        print(
            f"  Missing Field: "
            f"{row.workflow_state_field}"
        )

        print("  ACTION: AUDIT ONLY")


# ============================================================
# 6. NOTIFICATIONS
# ============================================================

section("6. NOTIFICATION AUDIT")

notifications = frappe.get_all(
    "Notification",
    filters={
        "document_type": ["in", murasalat_doctypes],
    },
    fields=[
        "name",
        "document_type",
        "condition",
        "message",
    ],
)

for row in notifications:

    text = (
        (row.condition or "")
        + "\n"
        + (row.message or "")
    )

    legacy_fields = contains_legacy_field(text)

    if legacy_fields:

        item = {
            "name": row.name,
            "doctype": row.document_type,
            "legacy_fields": legacy_fields,
        }

        report["notifications"].append(item)

        print("\nLEGACY NOTIFICATION")
        print(f"  Name: {row.name}")
        print(f"  DocType: {row.document_type}")
        print(f"  Fields: {legacy_fields}")

        print("  ACTION: AUDIT ONLY")


# ============================================================
# 7. PRINT FORMAT AUDIT
# ============================================================

section("7. PRINT FORMAT AUDIT")

print_formats = frappe.get_all(
    "Print Format",
    filters={
        "doc_type": ["in", murasalat_doctypes],
    },
    fields=[
        "name",
        "doc_type",
        "html",
    ],
)

for row in print_formats:

    legacy_fields = contains_legacy_field(row.html)

    if legacy_fields:

        item = {
            "name": row.name,
            "doctype": row.doc_type,
            "legacy_fields": legacy_fields,
        }

        report["print_formats"].append(item)

        print("\nLEGACY PRINT FORMAT REFERENCE")
        print(f"  Name: {row.name}")
        print(f"  DocType: {row.doc_type}")
        print(f"  Fields: {legacy_fields}")

        print("  ACTION: AUDIT ONLY")


# ============================================================
# 8. REPORT AUDIT
# ============================================================

section("8. REPORT AUDIT")

reports = frappe.get_all(
    "Report",
    filters={
        "ref_doctype": ["in", murasalat_doctypes],
    },
    fields=[
        "name",
        "ref_doctype",
        "report_type",
        "query",
    ],
)

for row in reports:

    legacy_fields = contains_legacy_field(row.query)

    if legacy_fields:

        item = {
            "name": row.name,
            "doctype": row.ref_doctype,
            "report_type": row.report_type,
            "legacy_fields": legacy_fields,
        }

        report["reports"].append(item)

        print("\nLEGACY REPORT REFERENCE")
        print(f"  Name: {row.name}")
        print(f"  DocType: {row.ref_doctype}")
        print(f"  Fields: {legacy_fields}")

        print("  ACTION: AUDIT ONLY")


# ============================================================
# 9. ORPHAN PERMISSION LEVELS
# ============================================================

section("9. PERMISSION LEVEL AUDIT")

for doctype in murasalat_doctypes:

    meta = frappe.get_meta(doctype)

    used_permlevels = {
        int(df.permlevel or 0)
        for df in meta.fields
        if df.fieldname
    }

    permissions = frappe.get_all(
        "DocPerm",
        filters={
            "parent": doctype,
        },
        fields=[
            "name",
            "role",
            "permlevel",
            "read",
            "write",
            "create",
            "delete",
        ],
    )

    for perm in permissions:

        permlevel = int(perm.permlevel or 0)

        if (
            permlevel > 0
            and permlevel not in used_permlevels
        ):

            item = {
                "name": perm.name,
                "doctype": doctype,
                "role": perm.role,
                "permlevel": permlevel,
            }

            report["orphan_permission_levels"].append(item)

            print("\nORPHAN PERMISSION LEVEL")
            print(f"  DocType: {doctype}")
            print(f"  Role: {perm.role}")
            print(f"  Permlevel: {permlevel}")

            print(
                "  ACTION: AUDIT ONLY "
                "(permissions are not automatically deleted)"
            )


# ============================================================
# CLEANUP / COMMIT
# ============================================================

section("10. CLEANUP SUMMARY")

print("\nDeleted:")

for row in report["deleted"]:
    print(
        f"  - {row['doctype']} -> {row['name']}"
    )

print("\nFailed:")

for row in report["failed"]:
    print(
        f"  - {row['doctype']} -> {row['name']}"
    )


if APPLY_CHANGES:

    section("APPLYING CHANGES")

    frappe.db.commit()

    frappe.clear_cache()

    for doctype in murasalat_doctypes:
        frappe.clear_document_cache(doctype)

    print("\nDatabase changes committed.")
    print("Frappe cache cleared.")

else:

    section("DRY RUN COMPLETE")

    print(
        "\nNo records were deleted because "
        "APPLY_CHANGES = False"
    )


# ============================================================
# FINAL REPORT
# ============================================================

section("FINAL AUDIT REPORT")

print(
    json.dumps(
        report,
        ensure_ascii=False,
        indent=2,
        default=str,
    )
)

print("\nDONE")
def execute():
    pass