
frappe.query_reports["Murasalat Employee Productivity"] = {
  filters: [
    {
      fieldname: "organization",
      label: "Department",
      fieldtype: "Link",
      options: "Department",
    },
    {
      fieldname: "from_date",
      label: "From",
      fieldtype: "Date",
    },
    {
      fieldname: "to_date",
      label: "To",
      fieldtype: "Date",
    },
  ],
};

