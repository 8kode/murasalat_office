frappe.query_reports["Murasalat Work Queue"] = {
  filters: [
    {fieldname: "organization", label: __("Organization Queue"), fieldtype: "Link", options: "Murasalat Organization Entity"},
    {fieldname: "user", label: __("User Queue"), fieldtype: "Link", options: "User"}
  ]
};
