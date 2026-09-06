app_name = "murasalat_office"
app_title = "Murasalat Office"
app_publisher = "QupNext"
app_description = "Administrative Correspondence Management System"
app_email = "qupnext.erp@gmail.com"
app_license = "mit"

fixtures = [
    {
        "dt": "Workspace Sidebar",
        "filters": [["name", "like", "Murasalat Office%"]],
    },
    {
        "dt": "Desktop Icon",
        "filters": [["name", "like", "Murasalat Office%"]],
    },
    {
        "dt": "Workflow State",
        "filters": [["name", "like", "Murasalat%"]],
    },
    {
        "dt": "Workflow",
        "filters": [["workflow_name", "like", "Murasalat%"]],
    },
    {
        "dt": "Workflow Action Master",
        "filters": [["name", "in", [
            "Register", "Close", "Reopen", "Cancel",
            "Send", "Mark Received", "Start Processing",
            "Complete", "Return", "Withdraw",
        ]]],
    },
]
