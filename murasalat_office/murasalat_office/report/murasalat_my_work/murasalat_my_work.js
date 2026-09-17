frappe.query_reports["Murasalat My Work"] = {
    onload(report) {
        report.page.add_inner_button(__("New Referral"), () => {
            frappe.new_doc("Murasalat Referral");
        });
    },
};