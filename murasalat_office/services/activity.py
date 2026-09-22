"""The single implementation of the activity-trail append.

Both the document controller and the lifecycle service record events in the activity
table. Having one implementation keeps the two from drifting apart — they previously
disagreed about argument order, which is the kind of difference that stays invisible
until an event records the wrong organization.
"""
import frappe
from frappe.utils import now_datetime


def append_activity(doc, activity_type, details=None, referral=None):
    """Append an activity to the in-memory document.

    Operating on the document (rather than the database) means the row participates in
    the caller's own save/Workflow transaction.
    """
    doc.append(
        "activities",
        {
            "activity_type": activity_type,
            "activity_on": now_datetime(),
            "actor": frappe.session.user,
            "organization": (
                referral.get("recipient_department")
                if referral and referral.get("recipient_department")
                else doc.get("current_holder")
            ),
            "referral_number": (
                referral.get("referral_number")
                if referral
                else None
            ),
            "details": details,
        },
    )
