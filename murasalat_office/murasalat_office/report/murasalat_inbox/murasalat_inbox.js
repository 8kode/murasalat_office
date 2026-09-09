frappe.query_reports["Murasalat Inbox"] = {
  filters: [
    {
      fieldname: "scope",
      label: __("Scope"),
      fieldtype: "Select",
      options: ["My Work", "My Organization", "Delegated to Me", "All Visible"],
      default: "My Work",
      reqd: 1,
    },
    {
      fieldname: "workflow_state",
      label: __("Workflow State"),
      fieldtype: "Data",
    },
    {
      fieldname: "due_only",
      label: __("Due Today or Earlier"),
      fieldtype: "Check",
      default: 0,
    },
  ],
};
