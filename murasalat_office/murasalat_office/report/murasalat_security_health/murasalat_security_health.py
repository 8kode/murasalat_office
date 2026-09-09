from murasalat_office.services.governance import governance_health


def execute(filters=None):
    columns = [
        {"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 90},
        {"label": "Check", "fieldname": "title", "fieldtype": "Data", "width": 260},
        {"label": "Details", "fieldname": "details", "fieldtype": "Text", "width": 420},
        {"label": "Remediation", "fieldname": "remediation", "fieldtype": "Text", "width": 420},
    ]
    return columns, governance_health()["checks"]
