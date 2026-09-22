"""Permission-aware referral inbox using native Frappe permissions.

The inbox represents OPEN referral work. Completed referrals are excluded from
all inbox scopes.
"""

import frappe
from frappe import _
from frappe.utils import getdate, today

from murasalat_office.services.reporting import enrich_with_correspondence
from murasalat_office.services.lifecycle import OPEN_REFERRAL_FILTERS


REFERRAL_FIELDS = [
    "correspondence",
    "name as referral_id",
    "referral_number",
    "recipient_type",
    "recipient_department",
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
    "correspondence_direction",
    "workflow_state as correspondence_status",
    "confidentiality",
    "importance",
    "current_holder",
]


def execute(filters=None):
    filters = frappe._dict(filters or {})

    user = frappe.session.user
    scope = filters.get("scope") or "My Work"
    due_only = filters.get("due_only")
    workflow_state = filters.get("workflow_state")

    base_filters = list(OPEN_REFERRAL_FILTERS)

    if workflow_state:
        base_filters.append(
            ["workflow_state", "=", workflow_state]
        )

    if due_only:
        base_filters.extend(
            [
                ["due_date", "is", "set"],
                ["due_date", "<=", today()],
            ]
        )

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
            ["recipient_type", "=", "Department"],
            ["recipient_department", "in", memberships],
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

        data = _query_delegated_referrals(
            delegations,
            base_filters,
        )

    elif scope == "All Visible":
        data = _query_referrals(base_filters)

    else:
        frappe.throw(
            _("Unknown inbox scope: {0}").format(scope)
        )

    enrich_with_correspondence(
        data,
        CORRESPONDENCE_FIELDS,
    )

    for row in data:
        row["attention"] = _attention(row)

        row["is_overdue"] = (
            1
            if row.due_date
            and getdate(row.due_date) < getdate(today())
            else 0
        )

    data.sort(
        key=lambda row: (
            row.due_date or "9999-12-31",
            row.get("modified") or "",
        )
    )

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
    grouped = {}

    for delegation in delegations or []:
        delegator = delegation.get("delegator")
        organization = delegation.get("organization")

        if not delegator:
            continue

        grouped.setdefault(
            delegator,
            set(),
        ).add(
            organization or ""
        )

    return grouped


def _query_delegated_referrals(delegations, base_filters):
    grouped = _group_delegations(delegations)

    if not grouped:
        return []

    restricted_orgs = sorted(
        {
            organization
            for organizations in grouped.values()
            for organization in organizations
            if organization
        }
    )

    correspondence_by_org = {}

    if restricted_orgs:
        correspondence_rows = frappe.get_list(
            "Murasalat Correspondence",
            filters={
                "originating_organization": [
                    "in",
                    restricted_orgs,
                ]
            },
            fields=[
                "name",
                "originating_organization",
            ],
            ignore_permissions=False,
            limit_page_length=0,
        )

        for row in correspondence_rows:
            correspondence_by_org.setdefault(
                row.get("originating_organization"),
                set(),
            ).add(row.get("name"))

    rows_by_name = {}

    if restricted_orgs:
        organization_rows = _query_referrals(
            base_filters
            + [
                ["recipient_type", "=", "Department"],
                [
                    "recipient_department",
                    "in",
                    restricted_orgs,
                ],
            ]
        )

        for row in organization_rows:
            rows_by_name[row.referral_id] = row

    for delegator, organizations in grouped.items():
        unrestricted = "" in organizations

        if unrestricted:
            rows = _query_referrals(
                base_filters
                + [
                    ["recipient_type", "=", "User"],
                    ["recipient_user", "=", delegator],
                ]
            )

        else:
            scoped_names = sorted(
                {
                    name
                    for organization in organizations
                    if organization
                    for name in correspondence_by_org.get(
                        organization,
                        set(),
                    )
                }
            )

            rows = []

            if scoped_names:
                rows = _query_referrals(
                    base_filters
                    + [
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
        {
            "label": _("Attention"),
            "fieldname": "attention",
            "fieldtype": "Data",
            "width": 130,
        },
        {
            "label": _("Correspondence"),
            "fieldname": "correspondence",
            "fieldtype": "Link",
            "options": "Murasalat Correspondence",
            "width": 170,
        },
        {
            "label": _("Subject"),
            "fieldname": "subject",
            "fieldtype": "Data",
            "width": 260,
        },
        {
            "label": _("Referral"),
            "fieldname": "referral_number",
            "fieldtype": "Data",
            "width": 120,
        },
        {
            "label": _("Recipient Type"),
            "fieldname": "recipient_type",
            "fieldtype": "Data",
            "width": 130,
        },
        {
            "label": _("Recipient Department"),
            "fieldname": "recipient_department",
            "fieldtype": "Link",
            "options": "Department",
            "width": 180,
        },
        {
            "label": _("Recipient User"),
            "fieldname": "recipient_user",
            "fieldtype": "Link",
            "options": "User",
            "width": 180,
        },
        {
            "label": _("Direction"),
            "fieldname": "direction",
            "fieldtype": "Link",
            "options": "Murasalat Referral Direction",
            "width": 150,
        },
        {
            "label": _("Workflow State"),
            "fieldname": "referral_workflow_state",
            "fieldtype": "Data",
            "width": 160,
        },
        {
            "label": _("Due Date"),
            "fieldname": "due_date",
            "fieldtype": "Date",
            "width": 110,
        },
        {
            "label": _("Current Department"),
            "fieldname": "current_holder",
            "fieldtype": "Link",
            "options": "Department",
            "width": 180,
        },
        {
            "label": _("Instructions"),
            "fieldname": "instructions",
            "fieldtype": "Small Text",
            "width": 260,
        },
    ]


def _attention(row):
    if (
        row.due_date
        and getdate(row.due_date) < getdate(today())
    ):
        return _("Overdue")

    if (
        row.due_date
        and getdate(row.due_date) == getdate(today())
    ):
        return _("Due Today")

    return row.referral_workflow_state or _(
        "Unassigned Workflow State"
    )


def _summary(data):
    return [
        {
            "value": len(data),
            "label": _("Visible Open Referrals"),
            "datatype": "Int",
        },
        {
            "value": sum(
                1
                for row in data
                if row.is_overdue
            ),
            "label": _("Overdue"),
            "datatype": "Int",
            "indicator": "Red",
        },
        {
            "value": sum(
                1
                for row in data
                if row.due_date
                and getdate(row.due_date) == getdate(today())
            ),
            "label": _("Due Today"),
            "datatype": "Int",
            "indicator": "Orange",
        },
    ]


def _result(data):
    return _columns(), data, None, _summary(data)


def _empty_result():
    return _result([])