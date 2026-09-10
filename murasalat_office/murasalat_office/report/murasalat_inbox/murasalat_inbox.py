"""Permission-aware referral inbox using native Frappe permissions."""

import frappe
from frappe.utils import getdate, today

from murasalat_office.services.reporting import enrich_with_correspondence


REFERRAL_FIELDS = [
    "correspondence",
    "name as referral_id",
    "referral_number",
    "recipient_type",
    "recipient_organization",
    "recipient_user",
    "direction",
    "workflow_state as referral_workflow_state",
    "due_date",
    "instructions",
    "follow_up",
    "received_on",
    "completed_on",
]
CORRESPONDENCE_FIELDS = [
    "subject",
    "correspondence_type",
    "workflow_state as correspondence_status",
    "confidentiality",
    "importance",
    "current_holder",
    "current_holder_user",
]


def execute(filters=None):
    filters = frappe._dict(filters or {})
    user = frappe.session.user
    scope = filters.get("scope") or "My Work"
    due_only = filters.get("due_only")
    workflow_state = filters.get("workflow_state")

    base_filters = []
    if workflow_state:
        base_filters.append(["workflow_state", "=", workflow_state])
    if due_only:
        base_filters.append(["due_date", "is", "set"])
        base_filters.append(["due_date", "<=", today()])

    if scope == "My Work":
        referral_filters = base_filters + [
            ["recipient_type", "=", "User"],
            ["recipient_user", "=", user],
        ]
        data = _query_referrals(referral_filters)
    elif scope == "My Organization":
        membership_query = frappe.qb.get_query(
            "Murasalat User Organization Membership",
            fields=["organization"],
            filters=[
                ["user", "=", user],
                "and",
                ["enabled", "=", 1],
                "and",
                [
                    ["valid_from", "is", "not set"],
                    "or",
                    ["valid_from", "<=", today()],
                ],
                "and",
                [
                    ["valid_to", "is", "not set"],
                    "or",
                    ["valid_to", ">=", today()],
                ],
            ],
            ignore_permissions=False,
        )
        memberships = membership_query.run(pluck=True)
        if not memberships:
            return _empty_result()
        referral_filters = base_filters + [
            ["recipient_type", "=", "Organization"],
            ["recipient_organization", "in", memberships],
        ]
        data = _query_referrals(referral_filters)
    elif scope == "Delegated to Me":
        delegations = frappe.get_list(
            "Murasalat Delegation",
            filters={
                "delegate": user,
                "enabled": 1,
                "from_date": ["<=", today()],
                "to_date": [">=", today()],
            },
            fields=["delegator", "organization"],
            ignore_permissions=False,
            limit_page_length=0,
        )
        data = _query_delegated_referrals(delegations, base_filters)
    elif scope == "All Visible":
        data = _query_referrals(base_filters)
    else:
        frappe.throw(f"Unknown inbox scope: {scope}")

    # Linked correspondence is always read through Frappe's own permissions.
    enrich_with_correspondence(data, CORRESPONDENCE_FIELDS)
    for row in data:
        row["attention"] = _attention(row)
        row["is_overdue"] = 1 if row.due_date and getdate(row.due_date) < getdate(today()) else 0

    data.sort(key=lambda row: (row.due_date or "9999-12-31", row.get("modified") or ""), reverse=False)
    return _result(data)


def _query_referrals(filters, or_filters=None):
    query = frappe.qb.get_query(
        "Murasalat Referral",
        fields=REFERRAL_FIELDS + ["modified"],
        filters=filters,
        or_filters=or_filters,
        ignore_permissions=False,
        order_by="due_date asc, modified desc",
    )
    return query.run(as_dict=True)


def _group_delegations(delegations):
    """Group active delegations by delegator and preserve organization scopes."""
    grouped = {}
    for delegation in delegations or []:
        delegator = delegation.get("delegator")
        organization = delegation.get("organization")
        if not delegator:
            continue
        grouped.setdefault(delegator, set()).add(organization or "")
    return grouped


def _query_delegated_referrals(delegations, base_filters):
    """Resolve delegation scopes with batched permission-aware lookups.

    An empty organization means an unrestricted delegation for direct User
    referrals. A populated organization additionally delegates referrals addressed
    to that organization, and can scope direct User referrals by correspondence
    origin. Organization referrals are batched once for all delegated organizations.
    """
    grouped = _group_delegations(delegations)
    if not grouped:
        return []

    restricted_orgs = sorted({
        organization
        for organizations in grouped.values()
        for organization in organizations
        if organization
    })

    correspondence_by_org = {}
    if restricted_orgs:
        correspondence_rows = frappe.get_list(
            "Murasalat Correspondence",
            filters={"originating_organization": ["in", restricted_orgs]},
            fields=["name", "originating_organization"],
            ignore_permissions=False,
            limit_page_length=0,
        )
        for row in correspondence_rows:
            correspondence_by_org.setdefault(row.get("originating_organization"), set()).add(row.get("name"))

    rows_by_name = {}

    # Organization-targeted referrals are independent of the delegator identity,
    # so resolve all of them in one permission-aware query.
    organization_rows = []
    if restricted_orgs:
        organization_rows = _query_referrals(
            base_filters + [
                ["recipient_type", "=", "Organization"],
                ["recipient_organization", "in", restricted_orgs],
            ]
        )
        for row in organization_rows:
            rows_by_name[row.referral_id] = row

    for delegator, organizations in grouped.items():
        unrestricted = "" in organizations
        if unrestricted:
            rows = _query_referrals(
                base_filters + [
                    ["recipient_type", "=", "User"],
                    ["recipient_user", "=", delegator],
                ]
            )
        else:
            scoped_names = sorted({
                name
                for organization in organizations
                if organization
                for name in correspondence_by_org.get(organization, set())
            })
            rows = []
            if scoped_names:
                rows = _query_referrals(
                    base_filters + [
                        ["recipient_type", "=", "User"],
                        ["recipient_user", "=", delegator],
                        ["correspondence", "in", scoped_names],
                    ]
                )

        for row in rows:
            rows_by_name[row.referral_id] = row

    return list(rows_by_name.values())

def _columns():
    return [
        {"label": "Attention", "fieldname": "attention", "fieldtype": "Data", "width": 130},
        {"label": "Correspondence", "fieldname": "correspondence", "fieldtype": "Link", "options": "Murasalat Correspondence", "width": 170},
        {"label": "Subject", "fieldname": "subject", "fieldtype": "Data", "width": 260},
        {"label": "Referral", "fieldname": "referral_number", "fieldtype": "Data", "width": 120},
        {"label": "Direction", "fieldname": "direction", "fieldtype": "Link", "options": "Murasalat Referral Direction", "width": 150},
        {"label": "Workflow State", "fieldname": "referral_workflow_state", "fieldtype": "Data", "width": 160},
        {"label": "Due Date", "fieldname": "due_date", "fieldtype": "Date", "width": 110},
        {"label": "Current Organization", "fieldname": "current_holder", "fieldtype": "Link", "options": "Murasalat Organization Entity", "width": 180},
        {"label": "Current User", "fieldname": "current_holder_user", "fieldtype": "Link", "options": "User", "width": 180},
        {"label": "Instructions", "fieldname": "instructions", "fieldtype": "Small Text", "width": 260},
    ]


def _attention(row):
    if row.due_date and getdate(row.due_date) < getdate(today()):
        return "Overdue"
    if row.due_date and getdate(row.due_date) == getdate(today()):
        return "Due Today"
    return row.referral_workflow_state or "Unassigned Workflow State"


def _summary(data):
    return [
        {"value": len(data), "label": "Visible Referrals", "datatype": "Int"},
        {"value": sum(1 for d in data if d.is_overdue), "label": "Overdue by Due Date", "datatype": "Int", "indicator": "Red"},
        {"value": sum(1 for d in data if d.attention == "Due Today"), "label": "Due Today", "datatype": "Int", "indicator": "Orange"},
    ]


def _result(data):
    return _columns(), data, None, _summary(data)


def _empty_result():
    return _result([])
