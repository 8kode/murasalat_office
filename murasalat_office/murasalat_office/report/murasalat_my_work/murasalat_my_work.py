import frappe

def execute(filters=None):
    user=(filters or {}).get('user') or frappe.session.user
    columns=[
      {'label':'Correspondence','fieldname':'parent','fieldtype':'Link','options':'Murasalat Correspondence','width':180},
      {'label':'Referral','fieldname':'name','fieldtype':'Data','width':130},
      {'label':'Subject','fieldname':'subject','fieldtype':'Data','width':280},
      {'label':'Status','fieldname':'status','fieldtype':'Data','width':120},
      {'label':'Direction','fieldname':'direction','fieldtype':'Link','options':'Murasalat Referral Direction','width':150},
      {'label':'Due Date','fieldname':'due_date','fieldtype':'Date','width':110},
      {'label':'Follow Up','fieldname':'follow_up','fieldtype':'Check','width':90},
    ]
    data=frappe.db.sql('''
      select r.parent, r.name, c.subject, r.status, r.direction, r.due_date, r.follow_up
      from `tabMurasalat Referral` r
      join `tabMurasalat Correspondence` c on c.name=r.parent
      where r.recipient_user=%s and r.status not in ('Completed','Rejected','Withdrawn')
      order by r.due_date is null, r.due_date asc, r.modified desc
    ''', user, as_dict=True)
    return columns,data
