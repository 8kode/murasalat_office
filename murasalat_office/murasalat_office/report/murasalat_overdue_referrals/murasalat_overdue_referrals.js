frappe.query_reports["Murasalat Overdue Referrals"] = {
  filters: [
    {fieldname: "organization", label: "Recipient Organization", fieldtype: "Link", options: "Murasalat Organization Entity"},
    {fieldname: "user_filter", label: "Recipient User", fieldtype: "Link", options: "User"},
    {fieldname: "from_date", label: "Due Date From", fieldtype: "Date"}
  ]
};
