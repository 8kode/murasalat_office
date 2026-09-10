"""Small reporting helpers that preserve native Frappe permissions.

These helpers are deliberately not an authorization engine. They only enrich rows
that were already fetched with ``ignore_permissions=False`` by reading linked
DocTypes through Frappe's own permission-aware list API.
"""

import frappe


def visible_correspondence_map(names: list[str], fields: list[str]) -> dict[str, object]:
    """Return permission-aware correspondence rows keyed by document name."""
    names = sorted({name for name in names if name})
    if not names:
        return {}

    rows = frappe.get_list(
        "Murasalat Correspondence",
        filters={"name": ["in", names]},
        fields=["name", *fields],
        ignore_permissions=False,
        limit_page_length=0,
    )
    return {row.name: row for row in rows}


def enrich_with_correspondence(rows: list[dict], fields: list[str]) -> list[dict]:
    """Enrich referral rows from a permission-aware correspondence lookup.

    Missing correspondence rows never reveal linked-document fields. A neutral
    ``[Restricted]`` subject marker keeps the report understandable when the user
    can see the referral but cannot read the linked correspondence.
    """
    mapping = visible_correspondence_map(
        [row.get("correspondence") for row in rows],
        fields,
    )
    for row in rows:
        linked = mapping.get(row.get("correspondence"))
        if not linked:
            if "subject" in fields:
                row["subject"] = "[Restricted]"
            continue
        for field in fields:
            row[field] = linked.get(field)
    return rows
