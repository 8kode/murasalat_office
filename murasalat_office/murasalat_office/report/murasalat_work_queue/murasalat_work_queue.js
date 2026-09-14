
frappe.query_reports["Murasalat Work Queue"] = {
  filters: [
    {
      fieldname: "organization",
      label: __("Department Queue"),
      fieldtype: "Link",
      options: "Department",
    },
    {
      fieldname: "user",
      label: __("User Queue"),
      fieldtype: "Link",
      options: "User",
    },
  ],
};
