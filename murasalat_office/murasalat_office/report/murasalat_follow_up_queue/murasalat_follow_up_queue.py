import frappe
from murasalat_office.reporting import permission_condition


def execute(filters=None):
    columns=[
        {'label':'Correspondence','fieldname':'correspondence','fieldtype':'Link','options':'Murasalat Correspondence','width':180},
        {'label':'Subject','fieldname':'subject','fieldtype':'Data','width':280},
        {'label':'Recipient','fieldname':'recipient_user','fieldtype':'Link','options':'User','width':180},
        {'label':'Direction','fieldname':'direction','fieldtype':'Link','options':'Murasalat Referral Direction','width':150},
        {'label':'Workflow State','fieldname':'workflow_state','fieldtype':'Data','width':160},
        {'label':'Due Date','fieldname':'due_date','fieldtype':'Date','width':110},
    ]
    parent_condition, values = permission_condition('c', 'Murasalat Correspondence')
    referral_condition, referral_values = permission_condition('r', 'Murasalat Referral')
    values.update(referral_values)
    where=["r.follow_up=1", parent_condition, referral_condition]
    data=frappe.db.sql(
        "SELECT r.correspondence,c.subject,r.recipient_user,r.direction,r.due_date,r.workflow_state "
        "FROM `tabMurasalat Referral` r JOIN `tabMurasalat Correspondence` c ON c.name=r.correspondence "
        "WHERE "+" AND ".join(where)+" ORDER BY r.due_date IS NULL,r.due_date ASC,r.modified DESC",
        values, as_dict=True
    )
    return columns,data
