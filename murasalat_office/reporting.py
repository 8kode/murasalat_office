"""Helpers for SQL reports that preserve native Frappe visibility.

SQL reports cannot rely on ``permission_query_conditions`` because this app does
not define one. Instead, report queries are constrained by names returned from
Frappe's permission-aware ``get_list`` for every DocType whose fields are exposed.
"""
import frappe


def visible_names(doctype, filters=None):
    return frappe.get_list(
        doctype,
        filters=filters or {},
        pluck="name",
        ignore_permissions=False,
        limit_page_length=0,
    )


def permission_condition(alias, doctype, filters=None):
    names = visible_names(doctype, filters)
    key = f"visible_{doctype.lower().replace(' ', '_')}_{alias}"
    if not names:
        return "1=0", {key: ["__NO_VISIBLE_DOCUMENTS__"]}
    return f"{alias}.name IN %({key})s", {key: names}
