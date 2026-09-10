from frappe import _


def get_data():
    return {
        "fieldname": "correspondence",
        "non_standard_fieldnames": {
            "Murasalat Referral": "correspondence",
            "Murasalat Approval Request": "correspondence",
        },
        "transactions": [
            {"label": _("Referrals"), "items": ["Murasalat Referral"]},
            {"label": _("Approvals"), "items": ["Murasalat Approval Request"]},
        ],
    }
