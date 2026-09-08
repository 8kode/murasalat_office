frappe.query_reports["Murasalat Employee Productivity"] = {
  filters: [
    {fieldname: "organization", label: "Current Organization", fieldtype: "Link", options: "Murasalat Organization Entity"},
    {fieldname: "from_date", label: "From", fieldtype: "Date"},
    {fieldname: "to_date", label: "To", fieldtype: "Date"}
  ]
};
