# Software Requirements Specification — SRS

# Murasalat Office

## Administrative Correspondence and Transaction Management System

---

| Item                   | Value                     |
| ---------------------- | ------------------------- |
| System Name            | Murasalat Office          |
| System Type            | Custom Frappe Application |
| Core Platform          | Frappe Framework 16       |
| Optional Compatibility | ERPNext 16                |
| Document Version       | 1.1                       |
| Document Status        | Implementation Baseline   |
| Primary Language       | Arabic                    |
| Interface Direction    | RTL                       |
| Document Year          | 2026                      |
| System Owner           | __________________        |
| Implementation Vendor  | __________________        |
| Project Manager        | __________________        |
| Approval Date          | __________________        |

---

# Document Revision History

|Version|Date|Description|Prepared By|Approved By|
|---|---|---|---|---|
|1.0|2026|Initial product vision and functional scope|—|—|
|1.1|2026|Restructured requirements, finalized the data model, added permissions, acceptance criteria, and non-functional requirements|—|—|

---

# 1. Purpose of This Document

This document defines the functional, technical, security, and non-functional requirements of the **Murasalat Office** system.

It shall serve as the primary reference for:

- Business analysis.
- Solution design.
- Software development.
- Quality assurance.
- Deployment.
- User acceptance testing.
- Production acceptance.
- Future maintenance and enhancements.

No new functionality or material behavioral change shall be introduced into the system unless the following actions are completed:

1. The requirement is formally documented.
2. The target implementation phase is identified.
3. The impact on the data model is assessed.
4. The impact on permissions and confidentiality is assessed.
5. Acceptance criteria are added or updated.
6. The change is approved by the System Owner.

---

# 2. Vision

Murasalat Office shall provide an institutional platform for managing the complete lifecycle of administrative correspondence and transactions, from initial receipt or creation through processing, closure, and archiving.

The system is not intended to replace ERPNext or become a new enterprise resource planning system. It shall provide a specialized layer for managing:

- Incoming correspondence.
- Outgoing correspondence.
- Internal correspondence.
- External parties.
- Documents and attachments.
- Routing and referrals.
- Assignments and ownership.
- Actions and tasks.
- Due dates.
- Follow-up.
- Relationships between correspondence records.
- Search.
- Reports.
- Printing.
- Activity history.
- Permissions.
- Future archiving.

---

# 3. Core Principle

The correspondence record is the central business entity. An attached document is not itself the correspondence transaction.

```text
Correspondence
├── Identity
├── Classification
├── Parties
├── Departments
├── Attachments
├── Routing
├── Assignment
├── Actions
├── Deadlines
├── Workflow
├── Comments
├── Timeline
├── Relations
└── Reports
```

The correspondence record represents the complete business transaction, while a document represents a file or content item associated with that transaction.

Example:

```text
Correspondence:
IN-2026-00125

Subject:
Project Approval Request

Attachments:
request.pdf
technical-attachment.pdf
supporting-image.jpg
```

---

# 4. System Scope

## 4.1 Functions Included in the Core Release

The core release shall include:

1. Registration of incoming correspondence.
2. Registration of outgoing correspondence.
3. Registration of internal correspondence.
4. Automatic generation of official reference numbers.
5. External party management.
6. Internal organizational structure management.
7. Correspondence classification.
8. Priority and confidentiality levels.
9. File attachments.
10. Routing to a department or user.
11. Complete routing history.
12. Current ownership assignment.
13. Due-date management.
14. Status and workflow management.
15. Personal correspondence inbox.
16. Search and filtering.
17. Relationships between correspondence records.
18. Comments and change history.
19. Printing.
20. Basic reports.
21. User and department permissions.
22. Prevention of unauthorized deletion.

## 4.2 Functions Outside the Core Release

The following functions are not included in the core release:

- Optical Character Recognition, or OCR.
- Full-text search inside attachment contents.
- Automatic email intake.
- Certified digital signatures.
- A standalone mobile application.
- Government system integrations.
- A dedicated external search engine.
- Artificial intelligence features.
- Custom independent file storage.
- Automated record retention and destruction.
- Advanced file version management.

The architecture shall not prevent these capabilities from being added in future releases.

---

# 5. Mandatory Architectural Decisions

## 5.1 Unified Correspondence Entity

Incoming, outgoing, and internal correspondence shall be implemented in one primary DocType named:

```text
Murasalat Correspondence
```

The correspondence type shall be identified through:

```text
correspondence_type
```

Allowed values:

- Incoming.
- Outgoing.
- Internal.

The implementation team shall not create three independent applications or three fully duplicated models containing separate copies of shared functionality.

## 5.2 Official Number Separate from Internal Identifier

Each correspondence record shall have:

1. An internal unique identifier used by the application.
2. An official reference number displayed to users and included in printed documents.

The official number field shall be:

```text
reference_number
```

The official number shall not be issued while the correspondence is in Draft state. It shall be issued only when the record is officially registered or sent, depending on its correspondence type.

## 5.3 Platform

- The application shall be built on Frappe Framework 16.
- The application shall not modify Frappe or ERPNext core files.
- The application shall be installable on a standalone Frappe site.
- The application shall be compatible with ERPNext 16 when installed on the same site.
- The application shall not implement a separate authentication system.
- Standard Frappe capabilities for users, roles, sessions, attachments, printing, comments, and permissions shall be used wherever practical.

Frappe provides user accounts, roles, DocType permissions, permission levels, User Permissions, naming methods, assignments, notifications, and permission-aware attachments.  
References: [Users and Permissions](https://docs.frappe.io/framework/user/en/basics/users-and-permissions), [Naming](https://docs.frappe.io/framework/user/en/basics/doctypes/naming), [Assignments and ToDos](https://docs.frappe.io/framework/assignments-and-todos), [Attachments](https://docs.frappe.io/framework/user/en/desk/attachments).

---

# 6. Terms and Definitions

|Term|Definition|
|---|---|
|Correspondence|The primary administrative correspondence or transaction record|
|Incoming|Correspondence received from an external party|
|Outgoing|Correspondence issued to an external party|
|Internal|Correspondence exchanged between internal departments or employees|
|Party|An external organization, entity, or individual associated with correspondence|
|Department|An organizational unit within the institution|
|Routing|Formal forwarding of correspondence from one user or department to another|
|Assignment|Identification of the current user or department responsible for processing|
|Action|A required or completed business action associated with correspondence|
|ToDo|An operational task displayed to a user|
|Workflow State|The official business lifecycle state|
|Timeline|The chronological display of changes, comments, and events|
|Confidentiality|The access sensitivity classification of correspondence|
|Current Owner|The user currently responsible for the correspondence|
|Current Department|The department currently responsible for the correspondence|
|Official Number|The official institutional reference number|

---

# 7. Stakeholders

|Stakeholder|Responsibility|
|---|---|
|System Owner|Approves scope, policies, and major changes|
|Executive Management|Reviews executive reports and indicators|
|Correspondence Office|Registers incoming and outgoing correspondence|
|Department Managers|Route, monitor, complete, and close correspondence|
|Department Employees|Process assigned correspondence and tasks|
|Audit Team|Reviews records and audit history without modification|
|Information Technology|Operates, secures, backs up, and maintains the platform|
|Development Team|Implements the approved requirements|
|Quality Assurance Team|Validates the system against acceptance criteria|

---

# 8. System Roles

## 8.1 System Manager

Responsibilities:

- Manage technical settings.
- Manage users and roles.
- Perform authorized system administration.
- Support technical troubleshooting.

This role shall not be used as a normal operational role.

## 8.2 Murasalat Administrator

Responsibilities:

- Manage Murasalat Office settings.
- Manage correspondence categories, priorities, and confidentiality levels.
- Manage parties and departments.
- Access organization-wide reports where authorized.
- Perform approved exceptional operations.

## 8.3 Correspondence Clerk

Responsibilities:

- Create and register incoming correspondence.
- Create and register outgoing correspondence.
- Enter party information.
- Upload attachments.
- Print correspondence records.
- Correct draft records before official registration.

The Correspondence Clerk shall not delete registered correspondence.

## 8.4 Department User

Responsibilities:

- View correspondence within the user’s authorized scope.
- Receive or acknowledge routed correspondence.
- Record actions and comments.
- Complete assigned tasks.
- Route correspondence where organizational policy permits.

## 8.5 Department Manager

Responsibilities:

- View correspondence within the department’s scope.
- Route and reassign correspondence.
- Review correspondence.
- Complete and close correspondence.
- Reopen correspondence where authorized.

## 8.6 Executive Manager

Responsibilities:

- View correspondence within the authorized organizational hierarchy.
- Issue instructions.
- Approve or reject correspondence.
- Review executive reports.

## 8.7 Auditor

Responsibilities:

- Read authorized correspondence.
- Read routing and change history.
- Run authorized reports.
- Perform no operational modification.

---

# 9. Master Data

## 9.1 External Parties

A DocType named the following shall be created:

```text
Murasalat Party
```

Required fields:

|Field|Type|Mandatory|
|---|---|---|
|Party Name Arabic|Data|Yes|
|Party Name English|Data|No|
|Party Type|Link or Select|Yes|
|Short Name|Data|No|
|External Code|Data|No|
|Phone|Data|No|
|Email|Data|No|
|Address|Small Text|No|
|Contact Person|Data|No|
|Notes|Text|No|
|Active|Check|Yes|

Default party types:

- Government Entity.
- Ministry.
- Public Institution.
- Private Company.
- Non-Profit Organization.
- International Organization.
- Individual.
- Other.

Party types shall be administratively configurable and shall not be permanently hard-coded into the user interface.

## 9.2 Departments

A hierarchical DocType shall be created:

```text
Murasalat Department
```

Fields:

- Department Name Arabic.
- Department Name English.
- Department Code.
- Parent Department.
- Manager.
- Active.
- Notes.

The structure shall support:

- The primary institution.
- General directorates.
- Departments.
- Sections.
- Sub-units.
- Changes in department managers without losing historical records.

## 9.3 User Department Membership

The system shall support linking a user to:

- One primary department.
- Additional authorized departments where necessary.
- A job title or organizational capacity.
- Membership start date.
- Membership end date.
- Active status.

The system shall not rely only on a free-text department value stored on the User record.

## 9.4 Correspondence Categories

Correspondence categories shall be configurable master data.

Default examples:

- Letter.
- Request.
- Memorandum.
- Circular.
- Decision.
- Notification.
- Invitation.
- Report.
- Complaint.
- Response.
- Other.

## 9.5 Priorities

Default priority values:

- Normal.
- High.
- Urgent.
- Critical.

Critical may be disabled in the user interface during the first release, but the architecture shall support it.

## 9.6 Confidentiality Levels

Default confidentiality levels:

- Public.
- Internal.
- Confidential.
- Restricted.

Internal values shall be stored in English and displayed to users using Arabic translations.

---

# 10. Correspondence Data Model

## 10.1 Primary DocType

```text
Murasalat Correspondence
```

## 10.2 Common Fields

|Field|Type|Description|
|---|---|---|
|Internal ID|UUID or Name|Internal system identifier|
|Reference Number|Data/Unique|Official correspondence number|
|Correspondence Type|Select|Incoming, Outgoing, or Internal|
|Subject|Data|Correspondence subject|
|Category|Link|Correspondence classification|
|Description|Text Editor|Correspondence details|
|Priority|Select or Link|Priority level|
|Confidentiality|Select or Link|Confidentiality level|
|Workflow State|Link or Data|Official lifecycle state|
|Transaction Date|Date|Business date of the correspondence|
|Registration Date|Datetime|Official registration timestamp|
|Original Document Date|Date|Date shown on the original document|
|External Reference Number|Data|External party reference number|
|Due Date|Date or Datetime|Processing deadline|
|Current Department|Link|Currently responsible department|
|Current Owner|Link/User|Currently responsible user|
|Source Party|Link|Sending external party|
|Target Party|Link|Receiving external party|
|Source Department|Link|Sending internal department|
|Target Department|Link|Receiving internal department|
|Received By|Link/User|User who received the correspondence|
|Sent By|Link/User|User who sent the correspondence|
|Approved By|Link/User|User who approved the correspondence|
|Completed By|Link/User|User who completed processing|
|Completed On|Datetime|Completion timestamp|
|Closed By|Link/User|User who closed the correspondence|
|Closed On|Datetime|Closure timestamp|
|Cancel Reason|Small Text|Mandatory cancellation reason|
|Reopen Reason|Small Text|Mandatory reopening reason|
|Dispatch Method|Link or Select|Delivery or dispatch method|
|Is Overdue|Computed|Whether the correspondence is overdue|

## 10.3 Incoming Correspondence Fields

When `correspondence_type` is Incoming, the system shall display:

- Source Party.
- External Reference Number.
- Original Document Date.
- Received By.
- Receiving Department.
- Registration Date.

The following fields shall be mandatory before registration:

- Subject.
- Source Party.
- Transaction Date or Received Date.
- Category.
- Confidentiality.
- Receiving Department.

## 10.4 Outgoing Correspondence Fields

When `correspondence_type` is Outgoing, the system shall display:

- Target Party.
- Target Contact Person.
- Issuing Department.
- Responsible User.
- Dispatch Method.
- External Reference Number where applicable.
- Approval information.
- Sent Date.

The following fields shall be mandatory before sending:

- Subject.
- Target Party.
- Issuing Department.
- Category.
- Confidentiality.
- At least one outgoing document, unless organizational policy allows otherwise.
- Approval by an authorized user.

## 10.5 Internal Correspondence Fields

When `correspondence_type` is Internal, the system shall display:

- Source Department.
- Source User.
- Target Department.
- Target User.
- Required Action.
- Due Date.

The following fields shall be mandatory before sending:

- Subject.
- Source Department.
- Target Department or Target User.
- Category.
- Confidentiality.

---

# 11. Official Numbering

## 11.1 Numbering Patterns

```text
Incoming: IN-YYYY-NNNNN
Outgoing: OUT-YYYY-NNNNN
Internal: INT-YYYY-NNNNN
```

Examples:

```text
IN-2026-00001
OUT-2026-00001
INT-2026-00001
```

## 11.2 Numbering Rules

**REQ-NUM-001**  
An official number shall not be issued while the correspondence is in Draft state.

**REQ-NUM-002**  
The incoming number shall be issued when the Register action is completed.

**REQ-NUM-003**  
The outgoing number shall be issued when the correspondence is officially approved or sent, according to the approved system configuration.

**REQ-NUM-004**  
The internal number shall be issued when the Send action is completed.

**REQ-NUM-005**  
The official reference number shall be unique across the system.

**REQ-NUM-006**  
A separate sequence shall be maintained for each correspondence type and each Gregorian year.

**REQ-NUM-007**  
The reference number shall become immutable after issuance.

**REQ-NUM-008**  
A cancelled correspondence number shall not be reused.

**REQ-NUM-009**  
The sequence is not required to be completely gap-free.

**REQ-NUM-010**  
The correspondence type shall not be changed after issuance of the official number.

**REQ-NUM-011**  
The system shall prevent duplicate numbers during concurrent registration operations.

Frappe supports naming series and year-based patterns, but its standard numbering is not necessarily gap-safe when records are deleted. Therefore, this specification requires uniqueness and non-reuse rather than a strictly gap-free sequence.  
Reference: [Frappe Naming](https://docs.frappe.io/framework/user/en/basics/doctypes/naming).

---

# 12. External Reference Number

**REQ-EXT-001**  
The system shall support an external reference number for incoming and outgoing correspondence.

**REQ-EXT-002**  
The external reference number is not required to be globally unique.

**REQ-EXT-003**  
The system shall warn the user when the same external reference number already exists for the same party within a configurable period.

**REQ-EXT-004**  
The system shall support exact and partial search using the external reference number.

**REQ-EXT-005**  
Symbols, slashes, hyphens, and formatting from the original external number shall be preserved.

Example:

```text
Internal Reference:
IN-2026-00125

External Reference:
MOH/2026/451
```

---

# 13. Workflow

One field shall represent the official business status:

```text
workflow_state
```

A separate `status` field serving the same purpose shall not be created.

The Frappe `docstatus` value shall not be treated as a replacement for the business workflow state.

## 13.1 Incoming Correspondence Workflow

```text
Draft
→ Registered
→ Assigned
→ In Progress
→ Waiting
→ Completed
→ Closed
→ Archived
```

Alternative terminal state:

```text
Cancelled
```

Transitions:

|Current State|Action|Next State|Authorized Role|
|---|---|---|---|
|Draft|Register|Registered|Clerk or Manager|
|Registered|Route|Assigned|Clerk or Manager|
|Assigned|Start Processing|In Progress|Assignee|
|In Progress|Wait|Waiting|Assignee or Manager|
|Waiting|Resume|In Progress|Assignee or Manager|
|In Progress|Complete|Completed|Assignee or Manager|
|Completed|Close|Closed|Manager|
|Closed|Reopen|In Progress|Authorized Manager|
|Draft or Registered|Cancel|Cancelled|Manager|
|Closed|Archive|Archived|Future function or authorized role|

## 13.2 Outgoing Correspondence Workflow

```text
Draft
→ Under Review
→ Approved
→ Sent
→ Closed
```

Transitions:

|Current State|Action|Next State|Authorized Role|
|---|---|---|---|
|Draft|Submit for Review|Under Review|Clerk or User|
|Under Review|Return|Draft|Reviewer|
|Under Review|Approve|Approved|Manager|
|Approved|Mark as Sent|Sent|Clerk or Manager|
|Sent|Close|Closed|Manager|
|Closed|Reopen|Sent or Draft|Authorized Manager|
|Draft or Under Review|Cancel|Cancelled|Manager|

## 13.3 Internal Correspondence Workflow

```text
Draft
→ Sent
→ Received
→ In Progress
→ Completed
→ Closed
```

Transitions:

|Current State|Action|Next State|Authorized Role|
|---|---|---|---|
|Draft|Send|Sent|Sender|
|Sent|Acknowledge Receipt|Received|Recipient|
|Received|Start Processing|In Progress|Recipient|
|In Progress|Complete|Completed|Recipient|
|Completed|Close|Closed|Manager or Sender|
|Sent or Received|Return|Draft|Authorized Role|
|Draft or Sent|Cancel|Cancelled|Manager|

## 13.4 Workflow Rules

- Users shall not edit `workflow_state` directly.
- State changes shall occur only through approved transition actions.
- The system shall record the user and timestamp for each transition.
- Workflow conditions shall be enforced on the server.
- Unauthorized transitions shall be rejected even when requested through the API.
- Reopening shall require a reason.
- Cancellation shall require a reason.
- Closed correspondence shall not be cancelled without exceptional authorization.
- Cancellation shall not delete the official number, attachments, or Timeline.

---

# 14. Routing

A separate DocType shall be created:

```text
Murasalat Correspondence Routing
```

## 14.1 Fields

- Correspondence.
- From Department.
- From User.
- To Department.
- To User.
- Instruction.
- Priority.
- Routed On.
- Due Date.
- Routing Status.
- Accepted On.
- Completed On.
- Routed By.
- Cancellation Reason.
- Notes.

## 14.2 Routing States

- Pending.
- Received.
- In Progress.
- Completed.
- Returned.
- Cancelled.

## 14.3 Routing Requirements

**REQ-ROU-001**  
The system shall support routing to a department, a user, or both.

**REQ-ROU-002**  
All previous routing records shall be retained.

**REQ-ROU-003**  
A new routing action shall not overwrite an earlier routing record.

**REQ-ROU-004**  
Current Department and Current Owner shall be updated after successful routing.

**REQ-ROU-005**  
The routed correspondence shall appear in the recipient’s or department’s My Inbox.

**REQ-ROU-006**  
The routing action shall appear in the correspondence Timeline.

**REQ-ROU-007**  
Routing to an inactive user shall be rejected.

**REQ-ROU-008**  
The system shall validate the target user’s department membership unless the initiating user has override permission.

**REQ-ROU-009**  
Routing instructions shall be mandatory where required by organizational policy.

**REQ-ROU-010**  
Cancelling a routing record shall not delete its history.

---

# 15. Assignments, Tasks, and Actions

## 15.1 Assignment Definition

An Assignment identifies the user or department currently responsible for processing correspondence or performing a specific action.

## 15.2 Action Definition

An Action is a business activity required or performed on correspondence, such as:

- Study.
- Review.
- Prepare Response.
- Approve.
- Sign.
- Contact External Party.
- Request Information.
- Attach Document.

## 15.3 Action DocType

The following DocType shall be introduced in Phase 2:

```text
Murasalat Correspondence Action
```

Fields:

- Correspondence.
- Action Type.
- Description.
- Assigned Department.
- Assigned User.
- Priority.
- Due Date.
- Status.
- Started On.
- Completed On.
- Completed By.
- Completion Notes.
- Created By.
- Created On.

Action states:

- Pending.
- In Progress.
- Waiting.
- Completed.
- Cancelled.

## 15.4 ToDo Integration

The system may create a standard Frappe ToDo linked to a correspondence record or action to make the task visible in the user’s task list.

A ToDo shall not replace the institutional routing history.

The implementation shall prevent unintended inconsistency among:

- Current Owner.
- Routing.
- Action.
- ToDo.

Frappe provides linked ToDos with allocated users, due dates, and basic states. Date reminders require appropriate Notification configuration.  
References: [Assignments and ToDos](https://docs.frappe.io/framework/assignments-and-todos), [Notifications](https://docs.frappe.io/framework/notifications).

---

# 16. Correspondence Relationships

A DocType shall be created:

```text
Murasalat Correspondence Relation
```

## 16.1 Relationship Types

- Reply To.
- Replied By.
- Related To.
- Follow-up Of.
- Resulted In.
- References.
- Replaces.
- Superseded By.

## 16.2 Relationship Rules

- A correspondence record shall not be related to itself.
- Duplicate relationships shall be prevented.
- The relationship creator and creation date shall be recorded.
- Relationships shall be displayed when the correspondence record is opened.
- Access to the related record shall remain subject to the user’s permissions.
- A relationship shall not grant access to the related correspondence.
- Reverse relationships shall be displayed automatically where appropriate.

Example:

```text
OUT-2026-00231
Reply To
IN-2026-00125
```

---

# 17. Attachments and Documents

## 17.1 Core Release Requirements

The system shall:

- Use the standard Frappe File system.
- Store correspondence attachments as Private files.
- Link each file to its correspondence record.
- Deny file access to users who cannot read the related correspondence.
- Record attachment addition and authorized removal.
- Prevent ordinary deletion of official attachments after closure.
- Support multiple attachments.
- Display file name, file type, size, uploader, and upload timestamp.

## 17.2 Supported File Types

Default allowed file types:

- PDF.
- JPG.
- JPEG.
- PNG.
- DOCX.
- XLSX.
- PPTX.
- TXT.

The allowed extensions and maximum size shall be configurable.

The proposed default maximum size per file is:

```text
50 MB
```

Any change shall be approved by the System Administrator and infrastructure owner.

## 17.3 File Protection

- The system shall validate both file extension and content type.
- Unauthorized executable files shall be rejected.
- Malware scanning shall be integrated in production where the required scanning service is available.
- Sensitive file links shall not be sent to unauthorized recipients.
- File protection shall not depend only on secrecy of the URL.
- File preview and download shall be subject to correspondence permissions.

Frappe documentation states that access to attached files is associated with permission to read the linked document. Therefore, accurate correspondence permissions are essential to file protection.  
Reference: [Frappe Attachments](https://docs.frappe.io/framework/user/en/desk/attachments).

## 17.4 Document Versions

Advanced content versioning is outside Phase 1.

In Phase 3, the following DocType shall be introduced:

```text
Murasalat Correspondence Document
```

It shall support:

- Document Type.
- Document Number.
- Document Date.
- Version Number.
- Previous Version.
- Current Version.
- File.
- Confidentiality.
- Checksum.
- Created By.
- Created On.

Frappe record change tracking shall not be treated as a complete file-content version management system.  
Reference: [Document Versioning](https://docs.frappe.io/erpnext/document-versioning).

---

# 18. Timeline and Audit Trail

## 18.1 Events to Be Displayed

The Timeline shall include:

- Correspondence creation.
- Official number issuance.
- Workflow state changes.
- Routing.
- Routing receipt or acknowledgment.
- Current owner changes.
- Attachment addition.
- Authorized attachment removal.
- Comment creation.
- Changes to significant fields.
- Relationship creation.
- Relationship removal.
- Completion.
- Closure.
- Reopening.
- Cancellation.
- Archiving.

## 18.2 Event Information

Where applicable, each event shall include:

- User.
- Date and time.
- Event type.
- Previous value.
- New value.
- Description.
- IP address, where available and permitted by institutional policy.

## 18.3 Audit Rules

- Ordinary users shall not delete audit history.
- Track Changes shall be enabled for significant DocTypes.
- Comments shall not replace formal workflow or routing records.
- Routing, actions, and relationships shall be stored as independent records.
- API operations shall be audited in the same manner as user-interface operations.
- Dates and times shall be displayed according to the institution’s configured time zone.

---

# 19. Comments

- Authorized users shall be able to add comments.
- The system shall display the author, date, and time.
- Comments shall appear in the Timeline.
- A comment shall not change the correspondence workflow state.
- Comments shall not be used as substitutes for formal assignment.
- Comment deletion shall be restricted.
- Unsafe HTML or executable content shall be sanitized or rejected.
- Comment access shall follow the correspondence read permission.

---

# 20. Search

## 20.1 Basic Search Fields

Users shall be able to search by:

- Official reference number.
- External reference number.
- Subject.
- Party.
- Correspondence type.
- Correspondence category.
- Date.
- Workflow state.
- Priority.
- Confidentiality.
- Department.
- Current owner.
- Record creator.

## 20.2 Advanced Search

The system shall support combinations such as:

```text
Type = Incoming
Party = Ministry of Health
From Date = 2026-01-01
To Date = 2026-03-31
State = In Progress
Priority = Urgent
Current Department = Finance
```

## 20.3 Search Rules

- Search results shall not include records the user cannot read.
- Result counts shall not reveal unauthorized confidential records.
- Partial search shall be supported for subject and external reference number.
- Exact search shall be supported for official reference numbers.
- Frequently searched fields shall be indexed appropriately.
- Results shall support sorting by last update, transaction date, and due date.

## 20.4 Arabic Search

The search implementation shall support, where practical:

- Ignoring Arabic diacritics.
- Ignoring Arabic tatweel.
- Normalizing common forms of Alef for search.
- Handling Arabic and Western numerals.
- Case-insensitive English search.
- Preserving the original stored value for display.

## 20.5 Search Inside Attachments

Attachment content search is outside Phase 1.

A future implementation may use:

```text
File
→ Text Extraction or OCR
→ Search Index
→ Permission-Filtered Results
```

Frappe provides interfaces for indexing and full-text search. However, file text extraction, OCR, Arabic normalization, and permission-aware attachment indexing shall be implemented and tested as a separate phase.  
Reference: [FullTextSearch API](https://docs.frappe.io/framework/user/en/api/full-text-search).

---

# 21. My Inbox and Dashboards

## 21.1 My Inbox

My Inbox shall display:

- Correspondence routed directly to the user.
- Correspondence routed to the user’s department.
- New correspondence not yet acknowledged.
- Correspondence requiring action.
- Overdue correspondence.
- Correspondence due today.
- Correspondence currently waiting.

## 21.2 My Tasks

My Tasks shall display:

- Open tasks.
- Overdue tasks.
- Tasks due today.
- Recently completed tasks.

My Tasks shall be implemented in Phase 2.

## 21.3 Dashboard

The dashboard shall display, according to the current user’s permissions:

- Total incoming correspondence.
- Total outgoing correspondence.
- Total internal correspondence.
- In-progress correspondence.
- Overdue correspondence.
- Urgent correspondence.
- Correspondence awaiting action.
- Completed correspondence.
- Closed correspondence.

Dashboard totals shall not include records the current user cannot access.

---

# 22. Notifications

## 22.1 Phase 1 Notifications

The system shall support notifications for:

- Correspondence routed directly to a user.
- Correspondence routed to the user’s department.
- Change of Current Owner.
- Returned correspondence.
- A comment mentioning a user, if mention functionality is enabled.

## 22.2 Phase 2 Notifications

Phase 2 shall support:

- Task assignment.
- Approaching due date.
- Due date reached.
- Overdue task or correspondence.
- Review request.
- Approval request.
- Approval.
- Rejection.
- Task completion.

## 22.3 Notification Rules

- Notifications shall not disclose information beyond the recipient’s permissions.
- A notification link shall not grant additional access.
- Access shall be denied if the recipient no longer has permission to the record.
- Configurable notification types shall be capable of being disabled.
- The system shall avoid generating duplicate notifications for the same event.

Frappe Notifications can be triggered by document events, value changes, and date-based events and can be delivered through supported channels.  
Reference: [Frappe Notifications](https://docs.frappe.io/framework/notifications).

---

# 23. Permissions and Security

## 23.1 Permission Dimensions

Access shall be determined using:

- User.
- Role.
- Department.
- Department hierarchy.
- Correspondence type.
- Current Department.
- Current Owner.
- Workflow State.
- Confidentiality Level.
- Explicit Access, where required.

## 23.2 Operations Matrix

|Operation|Clerk|Department User|Manager|Auditor|Administrator|
|---|---|---|---|---|---|
|Create Draft|Yes|According to policy|Yes|No|Yes|
|Register Incoming|Yes|No|Yes|No|Yes|
|Prepare Outgoing|Yes|Yes|Yes|No|Yes|
|Approve Outgoing|No|No|Yes|No|Yes|
|Route|According to policy|According to policy|Yes|No|Yes|
|Edit Draft|Yes|According to ownership|Yes|No|Yes|
|Edit After Registration|Limited|Limited|Limited|No|Exceptional|
|Add Comment|Yes|Yes|Yes|No|Yes|
|Add Attachment|Yes|Yes|Yes|No|Yes|
|Delete Official Attachment|No|No|Exceptional|No|Exceptional|
|Complete Correspondence|No|According to assignment|Yes|No|Yes|
|Close Correspondence|No|No|Yes|No|Yes|
|Reopen Correspondence|No|No|By authorization|No|Yes|
|Cancel Correspondence|No|No|By authorization|No|Yes|
|Delete Registered Record|No|No|No|No|Disabled by default|
|View Audit History|Limited|Limited|Yes|Yes|Yes|
|Export|According to policy|According to policy|Yes|According to policy|Yes|
|Print|Yes|According to permission|Yes|According to policy|Yes|

## 23.3 Department Isolation

- An ordinary user shall see correspondence assigned to the user or the user’s authorized department according to policy.
- A manager may see correspondence belonging to the manager’s department and subordinate departments where hierarchical access is enabled.
- Department membership shall not automatically grant access to Restricted correspondence.
- Permissions shall apply to lists, forms, reports, search, APIs, print output, and file download.
- Security shall not rely only on hiding user-interface elements.

## 23.4 Confidentiality Rules

### Public

Available to internal users according to general role permissions.

### Internal

Available to users whose authorized business scope includes the correspondence.

### Confidential

Available only to:

- The creator, according to policy.
- The current department.
- The current owner.
- Authorized managers.
- Explicitly authorized users.

### Restricted

Available only to:

- Explicit access-list users.
- Designated security roles.
- Authorized system administrators under institutional policy.

## 23.5 Separate Permissions

The system shall independently control:

- Read.
- Write.
- Create.
- Delete.
- Print.
- Export.
- Share.
- Email.
- Download File.
- View Audit.
- Reopen.
- Cancel.
- Override Confidentiality.

Frappe supports separate permissions for operations such as reading, writing, deleting, printing, exporting, sharing, and emailing, in addition to User Permissions and permission levels.  
Reference: [Users and Permissions](https://docs.frappe.io/framework/user/en/basics/users-and-permissions).

---

# 24. Data Integrity

The system shall prevent:

- Duplicate official reference numbers.
- Registration without a subject.
- Registration without a correspondence type.
- Registration without a required date.
- Incoming registration without a source party.
- Outgoing sending without a target party.
- Internal sending without a target department or user.
- Routing to an inactive user.
- An action without a correspondence record.
- A correspondence record being related to itself.
- Duplicate correspondence relationships.
- Changing the correspondence type after official numbering.
- Modifying the official reference number.
- Unauthorized workflow transitions.
- Closure before mandatory completion conditions are met.
- Deletion of registered correspondence by ordinary users.
- File access without permission to the related correspondence.

All integrity rules shall be enforced on the server and shall not rely only on client-side JavaScript.

---

# 25. Closure, Cancellation, and Reopening

## 25.1 Closure

Before closure:

- The correspondence shall be Completed or Sent, depending on its type.
- No mandatory open tasks shall remain where this rule is enabled.
- The closing user and closure timestamp shall be recorded.
- Normal modification of significant fields shall be restricted.

## 25.2 Cancellation

- Cancellation shall not mean deletion.
- A cancellation reason shall be mandatory.
- The official reference number shall be retained.
- Attachments, relationships, and history shall be retained.
- The record shall appear as Cancelled in reports.
- The cancelled number shall never be reused.

## 25.3 Reopening

- Only authorized roles may reopen correspondence.
- A reopening reason shall be mandatory.
- The responsible user and timestamp shall be recorded.
- The record shall return to an appropriate workflow state.
- The reopening event shall appear in the Timeline.

---

# 26. Archiving and Retention

## 26.1 Definition of Archiving

Archiving does not mean deleting a record. It means moving a record to a non-operational state while retaining:

- Data.
- Attachments.
- Routing history.
- Actions.
- Comments.
- Relationships.
- Change history.

## 26.2 Core Release

- No automatic record deletion shall be implemented.
- No automatic attachment destruction shall be implemented.
- Closed correspondence shall remain searchable according to permissions.
- The Archived state shall be fully implemented in Phase 3.

## 26.3 Retention Policy

The institution shall approve the legal retention period before enabling any destruction functionality.

Until such approval:

```text
Retention Period = Indefinite
Automatic Destruction = Disabled
```

---

# 27. Reports

## 27.1 Phase 1 Reports

The following reports shall be provided:

1. Incoming Correspondence Report.
2. Outgoing Correspondence Report.
3. Internal Correspondence Report.
4. Correspondence by Workflow State.
5. Correspondence by Department.
6. Correspondence by Party.
7. Correspondence by Date Period.
8. Overdue Correspondence Report.
9. Urgent Correspondence Report.
10. Open Routing Report.
11. Closed Correspondence Report.
12. Cancelled Correspondence Report.

## 27.2 Common Report Filters

Reports shall support, as applicable:

- Date period.
- Correspondence type.
- Workflow state.
- Department.
- Party.
- User.
- Priority.
- Confidentiality.
- Overdue or not overdue.
- Category.

## 27.3 Future Management Reports

Future releases may include:

- Average Processing Time.
- Average Response Time.
- Overdue Rate.
- Completion Rate.
- Department Performance.
- User Workload.

Each performance indicator shall be formally defined before implementation. Waiting periods, holidays, cancelled records, and other exclusions shall be specified before employee or department performance is calculated.

---

# 28. Printing

An official Print Format shall be provided and shall include:

- Institution logo.
- Institution name.
- Correspondence type.
- Official reference number.
- External reference number.
- Date.
- Party.
- Department.
- Subject.
- Description.
- Priority.
- Confidentiality, according to policy.
- Responsible-user details.
- Attachment list.
- Approval information.
- Print date and time.
- Printing user, where required by institutional policy.

## 28.1 Printing Rules

- A4 page size shall be supported.
- RTL layout shall be supported.
- Arabic text shall not be truncated or incorrectly aligned.
- Unauthorized fields shall not be printed.
- Print permission shall be controlled independently.
- QR codes may be added in a future phase.
- PDF output shall be tested using supported browsers and the approved production environment.

Frappe Framework 16 provides Print Format capabilities and updated PDF generation options, including a Chrome-based PDF converter according to its version feature page.  
Reference: [Frappe Framework 16](https://frappe.io/framework/version-16).

---

# 29. Home Page and User Experience

## 29.1 Home Page

The home page shall provide the following primary shortcuts:

```text
┌──────────────────────────────────┐
│           Murasalat OFFICE            │
├──────────────────────────────────┤
│ Incoming        Outgoing         │
│ Internal        My Correspondence│
│ My Inbox        My Tasks         │
│ Due Today       Overdue          │
└──────────────────────────────────┘
```

## 29.2 User Experience Requirements

- The default interface shall be Arabic and RTL.
- Internal field names shall be in English.
- User-facing labels shall be displayed in Arabic.
- Frequently used fields shall appear near the top of the form.
- Fields shall be shown conditionally according to correspondence type.
- Irrelevant fields shall not be shown by default.
- The correspondence record shall provide one central page containing its essential information.
- Routing, relationships, and attachments shall be visible from the same page.
- The number of steps required to register correspondence shall be minimized.
- Validation messages shall be clear and provided in Arabic.
- A draft shall be saved without issuing an official number.
- Available action buttons shall depend on workflow state and user permission.

---

# 30. Localization

- The primary system language shall be Arabic.
- The primary interface direction shall be RTL.
- English may be enabled as a secondary language in a future release.
- Stable technical values shall be stored in English.
- Arabic translations shall be displayed to end users.
- The Gregorian calendar shall be used as the primary stored calendar.
- Hijri date display may be introduced later without replacing the original stored date.
- The system time zone shall be configurable.
- Server timestamps shall be stored consistently.
- Times shall be displayed according to institution or user settings.

---

# 31. Non-Functional Requirements

## 31.1 Performance

Performance shall be measured using a production-like environment and realistic test data.

Baseline targets:

|Operation|Target|
|---|---|
|Load first page of correspondence list|Under 2 seconds for 95% of requests|
|Open correspondence without large attachments|Under 3 seconds for 95% of requests|
|Save correspondence|Under 2 seconds for 95% of requests|
|Search indexed fields|Under 3 seconds for 95% of requests|
|Open My Inbox|Under 3 seconds|
|Generate a standard PDF|Under 10 seconds|
|Complete a workflow transition|Under 3 seconds|

Design assumptions:

- Up to 500,000 correspondence records.
- Up to 2,000,000 attachments.
- Up to 500 registered users.
- Up to 100 concurrent users.
- An average of three to five attachments per correspondence record.

If actual usage exceeds these assumptions, new load testing and index and storage reviews shall be performed.

## 31.2 Availability

The operational availability target shall be:

```text
99.5% per month
```

Approved scheduled maintenance shall be excluded.

## 31.3 Backup and Recovery

Backups shall include:

- Database.
- Public files.
- Private files.
- Site configuration.
- Application configuration required for recovery.

Recovery objectives:

```text
Recovery Point Objective, RPO: No more than 4 hours
Recovery Time Objective, RTO: No more than 8 hours
```

Final values shall be approved based on the selected infrastructure.

Periodic recovery testing shall be performed. Creating backups without testing restoration shall not be considered sufficient.

## 31.4 Security

- HTTPS shall be used in production.
- Passwords shall not be stored by the custom application.
- Frappe authentication shall be used.
- The principle of least privilege shall be applied.
- Secrets shall not be written to logs.
- API keys shall be protected.
- Session expiration shall be configured.
- Password policies shall be enforced.
- Login attempts shall be restricted or throttled.
- Administrator access shall be reviewed.
- Frappe and its dependencies shall be updated according to an approved security policy.
- Uploaded files shall be malware-scanned where an approved scanning service is available.

## 31.5 Browser Compatibility

The system shall support the latest two stable versions available at acceptance time of:

- Google Chrome.
- Microsoft Edge.
- Firefox, if approved by the institution.

Desktop use shall have priority. Basic mobile-browser usability shall be supported without requiring a standalone mobile application.

## 31.6 Maintainability

- The application shall use a modular structure.
- Standard DocTypes shall be used where appropriate.
- Core modifications shall be prohibited.
- Automated tests shall cover critical business rules.
- Public and significant functions shall be documented.
- Database and schema changes shall be delivered through migrations.
- Source code shall be maintained in version control.
- Code review shall be required.
- Separate Development, Staging, and Production environments shall be provided.

---

# 32. Logging and Monitoring

The system shall log:

- Server errors.
- Background job failures.
- Notification failures.
- File or PDF generation failures.
- Invalid workflow transition attempts.
- Sensitive administrative operations.
- Future integration failures.

Logs shall not contain:

- Passwords.
- Complete API secrets.
- Unnecessary confidential document contents.
- Session tokens.
- Excessive personal data.

---

# 33. API Requirements

## 33.1 Phase 1

A public custom business API is not required in Phase 1.

Use of the standard REST API shall not bypass:

- Permissions.
- Workflow rules.
- Data validation.
- Confidentiality controls.
- Deletion restrictions.

## 33.2 Phase 5

Future custom APIs may support:

- Creating correspondence.
- Querying correspondence status.
- Uploading attachments.
- Routing correspondence.
- Retrieving relationships.
- Integrating with external systems.

Future APIs shall use:

- Approved authentication.
- Rate limiting.
- Audit logging.
- Versioned endpoints.
- Idempotency controls for sensitive operations.

---

# 34. Implementation Phases

## Phase 1 — Core Operational System

Phase 1 shall include:

- Murasalat Correspondence.
- Incoming, Outgoing, and Internal types.
- Murasalat Party.
- Murasalat Department.
- Correspondence categories.
- Priority.
- Confidentiality.
- Official numbering.
- External reference numbers.
- Private attachments.
- Basic workflow.
- Basic routing.
- Current Owner and Current Department.
- Due Date.
- Basic My Inbox.
- Search and filters.
- Reply To and Related To relationships.
- Timeline.
- Comments.
- Printing.
- Basic permissions.
- Basic reports.
- Prevention of deletion after registration.

## Phase 2 — Workflow and Tasks

Phase 2 shall include:

- Correspondence Actions.
- ToDo integration.
- My Tasks.
- Due-date notifications.
- Escalation.
- Multi-level approvals.
- Advanced return and resubmission paths.
- Automatic assignment rules.

## Phase 3 — Advanced Management

Phase 3 shall include:

- Correspondence chains.
- Document metadata.
- File versioning.
- Advanced permissions.
- Explicit access lists.
- Archived state.
- Retention policies.
- Advanced reports.
- Performance indicators.

## Phase 4 — Digital Office

Phase 4 shall include:

- Email integration.
- Scanner intake.
- OCR.
- Full-text attachment search.
- QR codes and barcodes.
- Digital approval.
- Digital signatures.
- Advanced notifications.

## Phase 5 — Integrations

Phase 5 shall include:

- Business REST API.
- Mobile application.
- External systems.
- Government systems.
- Messaging platforms.
- AI services.

---

# 35. Primary Acceptance Criteria

## AC-001 — Create Draft

**Given:** The user has permission to create correspondence.  
**When:** The user creates and saves a new draft.  
**Then:**

- The record shall be saved.
- No official number shall be issued.
- The creator and creation time shall be recorded.
- The record shall only be visible to authorized users.

## AC-002 — Register Incoming Correspondence

**Given:** An Incoming correspondence draft contains all mandatory fields.  
**When:** The user performs Register.  
**Then:**

- A number matching `IN-YYYY-NNNNN` shall be issued.
- The number shall be unique.
- The state shall become Registered.
- The correspondence type and official number shall become immutable.
- The event shall be recorded in the Timeline.

## AC-003 — Send Outgoing Correspondence

**Given:** An Outgoing correspondence record is approved and complete.  
**When:** The user performs Mark as Sent.  
**Then:**

- The official outgoing number shall be issued if it has not already been issued according to approved policy.
- The target party, dispatch method, and sent date shall be saved.
- The state shall become Sent.
- The event shall be recorded in the Timeline.

## AC-004 — Send Internal Correspondence

**Given:** An Internal correspondence record contains a source and target department.  
**When:** The user performs Send.  
**Then:**

- A number matching `INT-YYYY-NNNNN` shall be issued.
- The correspondence shall appear in the receiving department’s inbox.
- The state shall become Sent.
- The sent timestamp shall be recorded.

## AC-005 — Prevent Duplicate Numbers

If an attempt is made to create an official number that already exists, the operation shall be rejected and no duplicate record shall be created.

## AC-006 — Route Correspondence

**Given:** The correspondence is registered and the user has routing permission.  
**When:** The user routes it to a department or user.  
**Then:**

- A new Routing record shall be created.
- Previous Routing records shall remain unchanged.
- Current Department or Current Owner shall be updated.
- The correspondence shall appear in the recipient’s My Inbox.
- The event shall be recorded in the Timeline.

## AC-007 — Reject Invalid Routing

The system shall reject routing to an inactive user or invalid organizational destination.

## AC-008 — Search by Official Number

When the full official number is entered, the corresponding record shall appear if the user has permission to read it.

## AC-009 — Search by External Number

The system shall support exact and partial search by external reference number.

## AC-010 — Permission Enforcement

A user from an unauthorized department shall not be able to:

- See the correspondence in a list.
- Open it using a direct URL.
- Retrieve it through the API.
- Download its attachments.
- Include it in report results.

## AC-011 — Restricted Confidentiality

Restricted correspondence shall only be visible to explicitly authorized users or approved security roles.

## AC-012 — File Protection

If the user does not have Read permission on the correspondence, the file download shall fail even if the user knows the file URL.

## AC-013 — Workflow Transition

A workflow state shall not be changed directly. It shall only be changed through a transition allowed for the current role, state, and correspondence type.

## AC-014 — Closure

A correspondence record shall only be closed by an authorized user after closure conditions are satisfied.

## AC-015 — Reopening

The system shall require a reopening reason and record the user, timestamp, and resulting state.

## AC-016 — Cancellation

Cancellation shall not delete the official number, attachments, routing records, relationships, or history.

## AC-017 — Incoming and Outgoing Relationship

The user shall be able to link an outgoing correspondence as a Reply To an incoming correspondence, and the relationship shall be displayed on both records subject to permissions.

## AC-018 — Timeline

The Timeline shall display at least:

- Creation.
- Registration.
- State changes.
- Routing.
- Attachment addition.
- Comments.
- Closure.
- Reopening.
- Cancellation.

## AC-019 — Printing

The system shall generate an Arabic RTL PDF containing the approved core data without exposing unauthorized information.

## AC-020 — Reports

Reports shall return results consistent with date, type, state, department, and user-permission filters.

## AC-021 — Performance

The system shall meet the performance objectives in Section 31 on the agreed acceptance environment.

## AC-022 — Deletion Prevention

An ordinary user or department manager shall not delete correspondence that has an official reference number.

## AC-023 — API Enforcement

Operations performed through the API shall apply the same permissions, workflow, confidentiality, and validation rules as the user interface.

## AC-024 — RTL Interface

The core Arabic interface, lists, forms, and Print Formats shall not contain material alignment, overlap, or text-direction defects.

---

# 36. Required Testing

## 36.1 Unit Tests

Automated unit tests shall cover:

- Official numbering.
- Required-field validation.
- Workflow transitions.
- Deletion prevention.
- Confidentiality rules.
- Routing.
- Relationships.
- Overdue calculation.

## 36.2 Integration Tests

Integration tests shall cover:

- Frappe permissions.
- File access.
- Workflow.
- Notifications.
- Print Formats.
- Reports.
- REST API behavior.

## 36.3 Security Tests

Security testing shall cover:

- Direct URL access.
- Direct file access.
- Department permission bypass.
- Workflow bypass through the API.
- Unauthorized export.
- Unauthorized printing.
- Restricted correspondence access.

## 36.4 Performance Tests

Performance tests shall cover:

- Search with high record volumes.
- List loading.
- Opening long Timelines.
- Reports.
- PDF generation.
- Concurrent users.

## 36.5 User Acceptance Testing

User acceptance testing shall include complete scenarios for:

- Incoming correspondence.
- Outgoing correspondence.
- Internal correspondence.
- Multi-level routing.
- Closure.
- Cancellation.
- Reopening.
- Confidential correspondence.
- Linking outgoing correspondence to incoming correspondence.

---

# 37. Required Development Deliverables

The development team shall deliver:

1. Source-code repository.
2. Installable Custom Frappe Application.
3. Installation instructions.
4. Upgrade instructions.
5. Roles and permission configuration.
6. Required DocTypes and fixtures.
7. Workflows.
8. Print Formats.
9. Reports.
10. Automated tests.
11. User manual.
12. System administrator manual.
13. Data-model documentation.
14. Configuration reference.
15. Backup and recovery plan.
16. Known-issues list.
17. Release notes.
18. Test data for the acceptance environment.
19. Performance test results.
20. User acceptance test closure report.

---

# 38. Production Readiness Conditions

The system shall not be considered ready for production until:

- All mandatory acceptance criteria pass.
- No unresolved Critical or High security vulnerability remains.
- Backup restoration has been tested successfully.
- The permissions matrix has been approved.
- Workflows have been approved.
- Print Formats have been approved.
- File-access permissions have been tested.
- Key users have received training.
- A separate Production environment has been prepared.
- A rollback plan has been approved.
- The deployed release has been documented.
- The System Owner has formally approved production deployment.

---

# 39. Explicit Exclusions

The project shall not build:

- A new ERP platform.
- An accounting system.
- A human-resources system.
- A CRM system.
- An inventory system.
- A financial system.
- A separate frontend in Phase 1.
- A separate authentication system.
- A separate workflow engine without a demonstrated need.
- Separate file storage without a demonstrated need.
- A separate search engine in Phase 1.
- A complete email management system in Phase 1.
- A digital-signature system in Phase 1.
- Security controls based only on hiding interface elements.

---

# 40. Constraints

- The application shall be compatible with Frappe Framework 16.
- Core-file modifications are prohibited.
- Upgrades shall be delivered through migrations.
- Permissions shall be enforced on the server.
- Sensitive files shall be Private.
- Historical relationships and routing records shall be retained.
- Official correspondence shall not be physically deleted.
- Important configurable classifications shall not be permanently hard-coded.
- Adding a future correspondence type shall not require rebuilding the application architecture.

---

# 41. Project Risks

|Risk|Impact|Mitigation|
|---|---|---|
|Complex department and confidentiality permissions|Unauthorized information disclosure|Detailed permission testing|
|Excessively complex workflows|Poor usability|Keep workflows simple and conditional|
|Large Timelines|Slow record opening|Pagination and lazy loading|
|Large attachment volumes|Storage exhaustion|File limits and storage policy|
|Duplicate parties|Inaccurate reports|Party master and duplicate detection|
|Excessive free-text fields|Weak search and reporting|Use Links and master data|
|Concurrent official numbering|Duplicate numbers|Unique constraints and transactional issuance|
|Confusion between Assignment and Routing|Inconsistent ownership|Clear definitions and one source of truth|
|Editing closed records|Weak auditability|Server validation and exceptional permissions|
|Arabic name variations|Reduced search accuracy|Search normalization while preserving original values|

---

# 42. Baseline Assumptions

This document adopts the following assumptions:

1. Each employee using the system has an individual Frappe user account.
2. The institution uses the Gregorian year for official numbering.
3. Cancelled numbers are not reused.
4. No automatic deletion is implemented in Phase 1.
5. Files are Private by default.
6. External Party master data is included in Phase 1.
7. Basic routing is included in Phase 1.
8. Basic incoming-to-outgoing relationships are included in Phase 1.
9. One unified DocType is used for all correspondence types.
10. One controlled workflow model supports conditional paths by correspondence type.
11. Record change tracking is not treated as file-content versioning.
12. ERPNext compatibility is optional and is not a mandatory functional dependency unless separately approved.

---

# 43. Definition of Success for the Core Release

The core release shall be considered successful when an authorized user can perform the following complete lifecycle:

```text
Create Correspondence
→ Enter Data
→ Attach Documents
→ Issue Official Number
→ Route Correspondence
→ Display It to the Recipient
→ Start Processing
→ Add Comments and Basic Actions
→ Link It to Another Correspondence
→ Complete It
→ Close It
→ Search for It
→ Review Its History
→ Print It
→ Include It in Reports
```

The system shall also ensure:

- Official reference numbers are not duplicated.
- Previous routing records are not lost.
- Official correspondence is not physically deleted.
- Files are not exposed to unauthorized users.
- Workflow rules cannot be bypassed.
- Correspondence does not appear outside its authorized organizational scope.
- Significant business events remain historically traceable.

---

# 44. Final Principle

Murasalat Office shall be:

> **Simple enough for daily use and strong enough for institutional growth.**

```text
Murasalat OFFICE
     │
     ▼
Correspondence
     │
     ├── Incoming
     ├── Outgoing
     └── Internal
     │
     ├── Parties
     ├── Departments
     ├── Attachments
     ├── Routing
     ├── Assignments
     ├── Actions
     ├── Relations
     ├── Workflow
     ├── Timeline
     ├── Search
     └── Reports
```

This document constitutes the project’s **Implementation Baseline**.

The development team shall implement the core release according to the mandatory requirements and acceptance criteria defined in this document. Any deviation, technical exception, or material design change shall be documented and approved before implementation.

---

# 45. Approval

|Role|Name|Signature|Date|
|---|---|---|---|
|System Owner||||
|Project Manager||||
|User Representative||||
|Technical Lead||||
|Development Team Representative||||
|Information Security Representative||||