import frappe

def execute(filters=None):
    columns=[{'label':'Correspondence','fieldname':'parent','fieldtype':'Link','options':'Murasalat Correspondence','width':180},{'label':'Subject','fieldname':'subject','fieldtype':'Data','width':280},{'label':'Recipient','fieldname':'recipient_user','fieldtype':'Link','options':'User','width':180},{'label':'Direction','fieldname':'direction','fieldtype':'Link','options':'Murasalat Referral Direction','width':150},{'label':'Status','fieldname':'status','fieldtype':'Data','width':120}]
    data=frappe.db.sql('''select r.parent,c.subject,r.recipient_user,r.direction,r.status from `tabMurasalat Referral` r join `tabMurasalat Correspondence` c on c.name=r.parent where r.due_date=curdate() and r.status not in ('Completed','Rejected','Withdrawn') order by r.modified desc''',as_dict=True)
    return columns,data
