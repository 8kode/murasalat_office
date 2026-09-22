from frappe import _


def get_data():
    """Native Connections for Murasalat Referral.

    A referral belongs to exactly one correspondence, so the reverse dashboard
    links back to that document through the standard native internal link.
    """
    return {
        "fieldname": "correspondence",
        "internal_links": {
            "Murasalat Correspondence": "correspondence",
        },
        "transactions": [
            {"label": _("Correspondence"), "items": ["Murasalat Correspondence"]},
        ],
    }
