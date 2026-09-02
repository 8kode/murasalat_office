app_name = "murasalat_office"
app_title = "Murasalat Office"
app_publisher = "QupNext"
app_description = "Administrative Correspondence Management System"
app_email = "qupnext.erp@gmail.com"
app_license = "mit"



fixtures = [
    
    {
        "dt": "Workspace",
        "filters": [["name", "like", "Murasalat Office%"]]
        # "filters": [["module", "=", "GSW Procurement"]]
        
 
    },
        {
        "dt": "Workspace Sidebar",
        "filters": [["name", "like", "Murasalat Office%"]]
        
    },

    {
        "dt": "Desktop Icon",
        "filters": [["name", "like", "Murasalat Office%"]]
        
    }

    # {
    #     "dt": "Custom Field",
    #     "filters": [["name", "like", "Murasalat Office%"]]
        
    # },
    # {
    #     "dt": "Custom Script",
    #     "filters": [["name", "like", "GESW%"]]
        
    # },
    # {
    #     "dt": "Property Setter",
    #     "filters": [["name", "like", "GESW%"]]
        
    # },
           ]   