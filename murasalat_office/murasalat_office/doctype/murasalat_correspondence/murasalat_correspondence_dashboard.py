from frappe import _


def get_data():
    return {
        "fieldname": "correspondence",
        "non_standard_fieldnames": {
            "Murasalat Referral": "correspondence",
        },
        "transactions": [
            {"label": _("Referrals"), "items": ["Murasalat Referral"]},
        ],
    }
