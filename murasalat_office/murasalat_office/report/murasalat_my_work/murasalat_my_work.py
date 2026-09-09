import frappe
from murasalat_office.reporting import permission_condition


def execute(filters=None):
    columns=[
        {'label':'Correspondence','fieldname':'correspondence','fieldtype':'Link','options':'Murasalat Correspondence','width':180},
        {'label':'Referral','fieldname':'name','fieldtype':'Link','options':'Murasalat Referral','width':130},
        {'label':'Subject','fieldname':'subject','fieldtype':'Data','width':280},
        {'label':'Workflow State','fieldname':'workflow_state','fieldtype':'Data','width':160},
        {'label':'Direction','fieldname':'direction','fieldtype':'Link','options':'Murasalat Referral Direction','width':150},
        {'label':'Due Date','fieldname':'due_date','fieldtype':'Date','width':110},
        {'label':'Follow Up','fieldname':'follow_up','fieldtype':'Check','width':90},
    ]
    parent_condition, values = permission_condition('c', 'Murasalat Correspondence')
    referral_condition, referral_values = permission_condition('r', 'Murasalat Referral')
    values.update(referral_values)
    where=["r.recipient_user=%(user)s", parent_condition, referral_condition]
    data=frappe.db.sql(
        "SELECT r.correspondence,r.name,c.subject,r.workflow_state,r.direction,r.due_date,r.follow_up "
        "FROM `tabMurasalat Referral` r JOIN `tabMurasalat Correspondence` c ON c.name=r.correspondence "
        "WHERE "+' AND '.join(where)+" ORDER BY r.due_date IS NULL,r.due_date ASC,r.modified DESC",
        values | {"user": frappe.session.user}, as_dict=True
    )
    return columns,data
