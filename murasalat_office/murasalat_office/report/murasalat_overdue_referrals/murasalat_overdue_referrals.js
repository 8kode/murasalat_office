
frappe.query_reports["Murasalat Overdue Referrals"] = {
  filters: [
    {
      fieldname: "organization",
      label: "Recipient Department",
      fieldtype: "Link",
      options: "Department",
    },
    {
      fieldname: "user_filter",
      label: "Recipient User",
      fieldtype: "Link",
      options: "User",
    },
    {
      fieldname: "from_date",
      label: "Due Date From",
      fieldtype: "Date",
    },
  ],
};

