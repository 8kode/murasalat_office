app_name = "murasalat_office"
app_title = "Murasalat Office"
app_publisher = "QupNext"
app_description = "Administrative Correspondence Management System"
app_email = "qupnext.erp@gmail.com"
app_license = "mit"



fixtures = [
    {
        "dt": "Workspace Sidebar",
        "filters": [["name", "like", "Murasalat Office%"]]
    },
    {
        "dt": "Desktop Icon",
        "filters": [["name", "like", "Murasalat Office%"]]
    }
]


doc_events = {
	"Murasalat Referral": {
		"on_update": (
			"murasalat_office.utils.routing."
			"sync_correspondence_summary"
		),
		"on_submit": (
			"murasalat_office.utils.routing."
			"sync_correspondence_summary"
		),
		"on_update_after_submit": (
			"murasalat_office.utils.routing."
			"sync_correspondence_summary"
		),
		"on_cancel": (
			"murasalat_office.utils.routing."
			"sync_correspondence_summary"
		),
		"after_delete": (
			"murasalat_office.utils.routing."
			"sync_correspondence_summary"
		),
	},
}

