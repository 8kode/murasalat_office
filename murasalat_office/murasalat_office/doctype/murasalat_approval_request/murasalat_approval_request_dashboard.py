from frappe import _


def get_data():
    return {
        "fieldname": "correspondence",
        "internal_links": {
            "Murasalat Correspondence": "correspondence",
        },
        "transactions": [
            {"label": _("Correspondence"), "items": ["Murasalat Correspondence"]},
        ],
    }
