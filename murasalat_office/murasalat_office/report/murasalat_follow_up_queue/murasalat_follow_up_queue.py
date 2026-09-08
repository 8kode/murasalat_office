import frappe

def execute(filters=None):
    columns=[
      {'label':'Correspondence','fieldname':'parent','fieldtype':'Link','options':'Murasalat Correspondence','width':180},
      {'label':'Subject','fieldname':'subject','fieldtype':'Data','width':280},
      {'label':'Recipient','fieldname':'recipient_user','fieldtype':'Link','options':'User','width':180},
      {'label':'Due Date','fieldname':'due_date','fieldtype':'Date','width':110},
      {'label':'Status','fieldname':'status','fieldtype':'Data','width':120},
    ]
    data=frappe.db.sql('''select r.parent,c.subject,r.recipient_user,r.due_date,r.status from `tabMurasalat Referral` r join `tabMurasalat Correspondence` c on c.name=r.parent where r.follow_up=1 and r.status not in ('Completed','Rejected','Withdrawn') order by r.due_date is null,r.due_date asc''',as_dict=True)
    return columns,data
