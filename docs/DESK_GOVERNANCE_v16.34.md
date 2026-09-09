# Desk Governance — Frappe 16.34.x / ERPNext 16.34.x

## Administrator checklist

### Permissions

Use **Role Permission Manager** to configure Read, Write, Create, Delete, Submit, Cancel, Amend, Report, Export, Import, Share, Print, Email, and other native permission options available for the DocType. Use User Permissions when access must be constrained by linked values.

### Workflows

Open **Settings → Workflow** and create or edit workflows for the Murasalat DocTypes. Workflow State names and transitions are not owned by the app.

Recommended setup sequence:

1. Create Roles / Role Profiles.
2. Configure DocType permissions.
3. Configure User Permissions where required.
4. Create Workflow States.
5. Create Workflow and Transition Rules.
6. Test each role through the Desk UI.
7. Change or replace the Workflow without modifying the app.

### Referral

`Murasalat Referral` is a standalone DocType. It can therefore have a separate Workflow and separate native permissions from `Murasalat Correspondence`.

### Important distinction

The app still performs data-integrity validation in Python. For example, a User referral must have a User recipient and an Organization referral must have an Organization recipient. These checks protect data consistency; they do not grant or deny a Role access.

## First-deployment quick start

Before business users begin testing, create at least one administrative role and one operational role in Desk, configure DocType permissions for the Murasalat DocTypes, add User Permissions where organizational visibility must be constrained, and then create the required Workflows. The application intentionally ships without business-role or workflow fixtures, so a new site starts with governance that must be configured by the site administrator.

A realistic first UAT flow is:

1. Create a correspondence as the intake/records user.
2. Move it through a Desk-configured Correspondence Workflow.
3. Create a standalone `Murasalat Referral` linked to that correspondence.
4. Configure and execute an independent Referral Workflow.
5. Verify the referral count and document links.
6. Repeat the same scenario as a user who has no permission to the documents and confirm the documents and reports remain invisible.
7. Change a Workflow State name or transition in Desk and repeat the test without modifying application code.

### Report scalability note

The SQL report layer uses permission-aware `get_list` to obtain visible document names and then applies those names as parameterized `IN` filters. This is deliberate because the application does not install a custom `permission_query_conditions` hook. For very large datasets, administrators should perform a production-sized UAT of report query size and database limits before rollout.

### Sealed correspondence attachments

Once a correspondence is sealed, its attachment set is part of the integrity snapshot. Adding, removing, or changing an attachment is therefore rejected. This prevents a sealed record's integrity hash from becoming stale; add or correct attachments before sealing.
