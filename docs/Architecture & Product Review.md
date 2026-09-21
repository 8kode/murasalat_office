# Murasalat Office — Architecture & Product Review
## Phase 1: Domain Model, Native Architecture, and Operational Design

**Baseline:** Murasalat Office v0.27.3 — Dev6  
**Target platform:** Frappe Framework 16.x + ERPNext 16.x  
**Review posture:** Native-First / Native-Governance

---

## 1. Executive Decision

The current application has a strong foundation and should **not** be rewritten.

The correct direction is a controlled architectural hardening that keeps the current core DocTypes while clarifying the responsibilities of:

- Correspondence
- Referral
- Workflow
- Assignment / ToDo
- Department ownership
- User ownership
- Delegation
- Audit / sealing
- Reporting
- Native Desk governance

The most important architectural decision is:

> **Correspondence is the official record. Referral is a unit of work transfer. ToDo/Assignment is personal execution. Workflow is governance.**

These concepts must remain related but must not become the same thing.

The application should continue to avoid a parallel authorization engine.

---

# 2. Current Domain Model

## 2.1 Primary business objects

### Murasalat Correspondence

Role:

> The authoritative institutional record of the correspondence transaction.

It owns:

- identity
- subject
- classification
- confidentiality
- importance
- external reference
- dates
- source/target parties
- attachments
- related correspondence
- organizational holder
- audit/sealing information

It should **not** become the task-management engine.

### Murasalat Referral

Role:

> A directed work instruction/transfer derived from a correspondence.

It owns:

- parent correspondence
- recipient
- direction
- importance
- due date
- instructions
- follow-up indicators
- sent/received/completed lifecycle

It is correctly modeled as a **standalone DocType**, not a child table.

This is one of the strongest architectural decisions in the current application.

### Murasalat Approval Request

Role:

> A governed approval object associated with a correspondence.

It should remain independent from Referral because approval and execution are different business concepts.

### Murasalat Delegation

Role:

> A period-bound organizational delegation relationship.

It should influence operational behavior only where the application explicitly needs delegation context. It must not become a second permissions system.

### Murasalat User Organization Membership

Role:

> Organizational relationship data between a User and a Department.

This should remain an organizational data model, not become an authorization engine.

---

# 3. Responsibility Boundaries

The target architecture should be:

```text
                    CORRESPONDENCE
                    Official Record
                          |
          +---------------+---------------+
          |               |               |
       Referral       Approval        Related Records
       Work Unit       Decision
          |
      Recipient
          |
   Assignment / ToDo
          |
      Personal Work
```

And separately:

```text
Workflow
   |
   +-- determines allowed business transitions

Python validation
   |
   +-- protects data integrity

Permissions in Desk
   |
   +-- determine who can read/write/create/etc.

Assignment / ToDo
   |
   +-- determine who currently has personal work

Delegation
   |
   +-- provides operational delegation context
```

This separation is the most important architectural principle for v0.28+.

---

# 4. Native Frappe Capabilities That Should Be Exploited More

Frappe Desk automatically provides List, Form, Report Builder, Calendar, Gantt, Kanban and other views from DocType metadata. The current application should therefore avoid building custom screens for capabilities already provided by Desk.

Official documentation:
- Desk and native views: https://docs.frappe.io/framework/user/en/desk
- DocTypes: https://docs.frappe.io/framework/user/en/basics/doctypes

## 4.1 Connections

The existing Correspondence ↔ Referral relationship is correctly implemented through a standalone Link field plus native Connections.

Do not replace this with a custom embedded referral UI.

Connections are specifically designed to expose linked documents and allow creation of related records.

Official documentation:
https://docs.frappe.io/framework/user/en/basics/doctypes/actions-and-links

## 4.2 Assignment Rules

ERPNext Assignment Rules can automatically assign documents to users, support Round Robin / Load Balancing / Based on Field, and can derive assignment due dates from a Date/Datetime field.

This creates a major opportunity:

> Do not write custom routing logic where Assignment Rules can perform the job.

Official documentation:
https://docs.frappe.io/erpnext/assignment-rule

## 4.3 Workflow Actions

Workflow Actions already provide a central list of pending workflow actions.

This should be treated as part of the user's work experience instead of recreating approval/action queues in custom code.

Official documentation:
https://docs.frappe.io/erpnext/workflow-actions

## 4.4 DocType Layouts

Current Frappe supports multiple layouts for the same DocType, including conditional visibility, labels, required/read-only properties, defaults and workspace integration.

This is a powerful future option, but it should **not** be introduced blindly.

For Murasalat Office, the first priority remains a clean default layout. Layout variants should only be introduced when there is a proven business need for distinct user personas or document states.

Official documentation:
https://docs.frappe.io/framework/doctypes/doctype-layout

---

# 5. Correspondence — Architectural Findings

## 5.1 What is correct

The current Correspondence DocType has a strong base:

- stable naming
- Track Changes
- Workflow State field
- classification
- parties
- related correspondence
- attachments
- operational ownership
- activity history
- sealing
- integrity hash

The use of a Data field for `workflow_state` is consistent with the Native-Governance principle because workflow values should remain Desk-governed rather than hard-coded in Python.

## 5.2 Main issue: too many meanings of ownership

The current model contains:

- `current_holder`
- `current_holder_user`
- `originating_organization`
- referral recipient
- ToDo assignee
- delegation context

These are not necessarily contradictory, but they represent different dimensions.

They should be interpreted as:

| Field / concept | Meaning |
|---|---|
| originating_organization | Where the correspondence originated in the institution |
| current_holder | Department currently responsible at organizational level |
| current_holder_user | Current personal work projection |
| Referral recipient organization | Department receiving a specific referral |
| Referral recipient user | User receiving a specific referral |
| ToDo assignee | Native personal assignment |
| Delegation | Temporary acting relationship |

The code must never treat all of these as synonyms.

---

# 6. Current Holder User — Important Architectural Risk

The current implementation derives `current_holder_user` from open ToDo records.

This is acceptable as a projection, but it must remain a projection.

The source of truth should be:

> Native ToDo / Assignment state.

The Correspondence field should be considered a convenience projection for reporting and display.

The synchronization logic should therefore be hardened around:

1. multiple open ToDos
2. reassignment
3. deletion
4. completion
5. duplicate ToDos
6. concurrent updates
7. permissions on the referenced Correspondence

The application should never use `current_holder_user` as a hidden permission decision.

---

# 7. Referral — Strategic Repositioning

Referral should be treated as the operational center of the application.

A correspondence can exist without a referral.

A referral represents:

> "This work has been directed to this recipient with these instructions and this deadline."

The resulting lifecycle is:

```text
Draft Referral
      |
      v
Sent
      |
      v
Received
      |
      v
In Progress
      |
      +---- Follow-up
      |
      v
Completed
```

The exact states must remain configurable in Desk.

The application code should validate data integrity such as:

- recipient type consistency
- required recipient
- required correspondence
- completion prerequisites

It should not impose a fixed set of workflow states.

---

# 8. Referral vs Assignment / ToDo

These must not be collapsed.

### Referral answers:

> What work was formally directed, to whom, and why?

### ToDo answers:

> Which user currently has a personal action to perform?

This distinction is crucial.

Example:

```text
Correspondence MO-00042
        |
        +-- Referral MR-00117
                |
                +-- Recipient Department: Legal
                |
                +-- Instruction: Review and provide opinion
                |
                +-- Due Date: 2026-09-20
                         |
                         +-- ToDo
                              |
                              +-- User: ahmed@example.com
```

This is a healthy separation.

---

# 9. Assignment Rules — Recommended Direction

The next implementation phase should test whether routing can be expressed using native Assignment Rules.

Potential scenarios:

### Scenario A — Direct user referral

Referral has `recipient_user`.

Native Assignment Rule can use a user Link field as the assignment source.

### Scenario B — Department referral

Referral has `recipient_department`.

This is more complex because a Department is not itself a User.

The preferred architecture is:

1. Referral records the organizational recipient.
2. Native assignment/routing configuration determines the responsible user(s).
3. Assignment is created as ToDo.
4. My Work reads the resulting personal assignment.

Do not introduce a custom "Department Permission Engine".

---

# 10. Workflow vs Lifecycle Code

This is one of the most important areas to harden.

Current code exposes lifecycle methods:

- register_correspondence
- close_correspondence
- seal_correspondence
- reopen_correspondence
- send_referral
- receive_referral
- complete_referral

The architecture should be:

### Workflow owns policy

Examples:

- who can register
- who can close
- who can approve
- who can send
- who can complete

### Code owns invariants and side effects

Examples:

- cannot complete an unreceived referral
- cannot change sealed identity fields
- update `registered_on`
- update `closed_on`
- update sealing metadata
- update receipt metadata
- append immutable operational history

Therefore:

> Workflow answers "may this transition occur?"
>
> Lifecycle code answers "what data consequences occur when it occurs?"

This preserves the user's Native-Governance requirement.

---

# 11. Sealing Architecture

The current integrity model is valuable and should be preserved.

The application calculates a canonical SHA-256 payload and protects selected fields after sealing.

This is appropriate because integrity is a data invariant rather than a business policy.

The immutable field list should remain explicit.

However, the next review should verify:

1. whether every business-critical field is included
2. whether `due_date` belongs in the integrity snapshot
3. whether `concerned_person` belongs in the snapshot
4. whether `notes` should be mutable after sealing
5. whether linked correspondence changes should invalidate the hash
6. whether referral changes should invalidate the correspondence hash
7. whether attachments are hashed consistently
8. whether a File can be changed outside the normal document save path
9. whether verification should distinguish metadata mismatch from file mismatch

Important principle:

> Sealing Correspondence should not accidentally imply that every related document becomes immutable.

---

# 12. Related Correspondence Links

The current `Murasalat Correspondence Link` child table is useful because it models relationships such as:

- Reply To
- Related To
- Parent
- Child
- Previous
- Next

This should remain.

However, the next hardening pass should consider:

- reciprocal link creation
- duplicate relationship semantics
- whether Parent/Child must be symmetric
- whether Reply To should automatically create a reverse relationship
- whether relationship types need ordering rules
- whether deleting one link should affect the other

Do not solve this with a custom graph engine.

---

# 13. External Party Model

Current model:

```text
Murasalat External Party Type
          |
          v
Murasalat External Party
```

Internal parties use Department.

This is acceptable, but the conceptual model should be normalized as:

```text
Party
 |
 +-- Internal Department
 |
 +-- External Party
```

without necessarily creating a new polymorphic DocType.

A new generic "Party" abstraction would add substantial complexity and would risk becoming a second framework.

Recommendation:

> Keep the current physical model unless real deployment proves that multiple external/internal party types require a unified abstraction.

The UX should instead make From/To semantics obvious.

---

# 14. Incoming / Outgoing / Internal Party Fields

The current field names reveal a real UX weakness:

- Incoming From
- Target Entry
- Incoming From on Outgoing
- Target Entity

The underlying fieldnames should remain stable for compatibility.

Labels should become semantic:

| Type | From | To |
|---|---|---|
| Incoming | External Party | Receiving Department |
| Outgoing | Sending Department | External Party |
| Internal | From Department | To Department |

This is a UX correction, not a data-model migration.

---

# 15. User Organization Membership

The current membership model is:

```text
User
Department
Enabled
Valid From
Valid To
```

This is good as organizational metadata.

Recommended rule:

> Membership must not silently grant read/write permission.

Permissions remain native Desk permissions.

Membership can safely be used for:

- default department
- routing context
- organizational reporting
- operational delegation context
- UI defaults

It should not be used as:

```python
if user belongs to department:
    allow read
```

unless that policy is explicitly intended to become a custom authorization mechanism — which conflicts with the project's architecture.

---

# 16. Delegation

Delegation should be treated as an operational relationship, not a replacement for permissions.

Current model has:

- delegator
- delegate
- from_date
- to_date
- enabled
- organization scope
- notes

This is a good base.

The next hardening step should ensure that reports such as My Work, Work Queue and Delegated Work apply the same delegation scope consistently.

Particularly:

> A delegation with Department Scope must not accidentally become a global delegation.

---

# 17. My Work — Target Product Definition

My Work should become the primary user work center.

It should answer:

> "What do I need to do now?"

Recommended logical categories:

```text
MY WORK

1. Overdue
2. Due Today
3. Due Soon
4. No Due Date
5. Follow-up Required
6. Pending Workflow Actions
```

The source data should be native:

- Referral
- ToDo / Assignment
- Workflow Actions

The custom report should only unify and present data that cannot reasonably be presented by native Desk views.

---

# 18. My Work Must Not Become an Authorization Layer

A report may filter:

```text
recipient_user == current user
```

but that does not replace DocPerm.

All underlying document retrieval must continue to respect Frappe permissions.

The current `visible_correspondence_map()` pattern is architecturally correct:

- retrieve referral rows
- permission-aware lookup of linked Correspondence
- use `[Restricted]` when the user can see the referral but not the linked Correspondence

This prevents information leakage through cross-DocType enrichment.

---

# 19. Reporting Architecture

Current reporting has a good principle:

> Reports are consumers of native permissions, not a parallel permissions engine.

This must be preserved.

The next performance review should focus on:

- large `IN` lists
- cross-DocType joins
- pagination
- indexes
- repeated linked-record lookups
- organization/delegation scope
- report filters

The correct optimization sequence is:

1. query design
2. native permission-aware retrieval
3. indexes where justified
4. pagination
5. caching only if demonstrated necessary

Do not add caching before measuring.

---

# 20. Workspace — Target Information Architecture

The Workspace should become an operational console:

```text
Murasalat Office

WORK
  My Work
  My Inbox
  Due Today
  Overdue
  Follow Up
  Workflow Actions

CREATE
  New Correspondence
  New Referral

OPERATIONS
  Correspondence
  Referrals
  Work Queue
  Referral Calendar

MANAGEMENT
  Employee Productivity
  Delegations

ADMINISTRATION
  Workflows
  User Permissions
  Security Health
```

The key principle is:

> Work first. Records second. Administration last.

---

# 21. Form UX — Target Hierarchy

The Correspondence form should visually communicate:

```text
IDENTITY
  Type
  Subject
  Status

CLASSIFICATION
  Transaction
  Confidentiality
  Importance

FROM / TO
  Sender
  Receiving Department
  or
  Sending Department
  External Recipient
  or
  From Department
  To Department

DATES
  External Reference
  Due Date

CONTENT
  Notes

RELATIONSHIPS
  Related Records
  Native Connections

ATTACHMENTS

AUDIT / SECURITY
  collapsed by default

ACTIVITY
  collapsed by default
```

The user should understand the business meaning without knowing the database field names.

---

# 22. What Should NOT Be Added

The architecture should explicitly reject:

- custom SPA dashboard
- custom permission engine
- custom workflow engine
- hard-coded workflow states
- shipped roles
- shipped DocPerm policy
- custom department authorization rules
- custom replacement for Connections
- custom replacement for ToDo
- custom replacement for Workflow Actions
- unnecessary generic Party abstraction
- unnecessary new DocTypes for UI convenience
- duplicated status fields

Every new feature should pass:

> "Can native Frappe/ERPNext already do this?"

If yes, use native first.

---

# 23. Highest-Priority Technical Risks

## P0 — Semantic ownership ambiguity

`current_holder`, `current_holder_user`, Referral recipient and ToDo assignment must have unambiguous meanings.

## P0 — Lifecycle/Workflow contract

Verify every lifecycle function is an invariant/side-effect helper and does not become hidden business policy.

## P0 — Delegation consistency

Audit all reports and work queues for consistent delegation scope.

## P1 — Assignment architecture

Test native Assignment Rules against the desired department/user routing model.

## P1 — Sealing completeness

Perform a field-by-field integrity snapshot review.

## P1 — Report scalability

Review Query Builder patterns, permission-aware enrichment and large name lists.

## P1 — Relationship semantics

Review Correspondence Link behavior and reciprocal relationship expectations.

## P2 — Advanced form layouts

Evaluate DocType Layout only after the base form UX is proven.

---

# 24. Recommended Target Architecture

```text
                         MURASALAT OFFICE
                                |
              +-----------------+------------------+
              |                 |                  |
        RECORD LAYER       WORK LAYER       GOVERNANCE LAYER
              |                 |                  |
       Correspondence        Referral          Workflow
              |                 |                  |
       Related Records      ToDo/Assign       Permissions
              |                 |                  |
       Attachments          My Work          User Permissions
              |                 |                  |
       Audit/Seal          Follow-up         Desk Configuration
              |
       Integrity Model
```

The system should therefore be understood as three layers:

### Record Layer

"What officially exists?"

### Work Layer

"Who must do what?"

### Governance Layer

"Who is allowed to make which transition?"

This is the cleanest conceptual model discovered in Phase 1.

---

# 25. Implementation Roadmap

## Phase A — Architecture Hardening

1. Formalize ownership semantics.
2. Review lifecycle methods.
3. Review delegation scope.
4. Review sealing fields.
5. Review correspondence relationship rules.
6. Review report permission boundaries.

## Phase B — Native Operations

1. Configure Assignment Rules.
2. Configure Workflow Actions.
3. Configure notifications where appropriate.
4. Configure user permissions from Desk.
5. Configure real institutional workflows from Desk.

## Phase C — Work-Centric UX

1. Finalize My Work.
2. Integrate pending Workflow Actions conceptually.
3. Improve Referral list.
4. Improve Referral calendar.
5. Improve Correspondence Connections.
6. Finalize Workspace.

## Phase D — Deployment Validation

1. Create a real institution.
2. Create departments.
3. Create users.
4. Configure permissions.
5. Configure workflows.
6. Configure assignment rules.
7. Create correspondence.
8. Create referral.
9. Test receipt.
10. Test completion.
11. Test delegation.
12. Test restricted access.
13. Test sealing.
14. Test reopening.
15. Test reporting.

---

# 26. Acceptance Criteria for the Architecture

The architecture is successful when:

### Governance

- Administrators can change Roles and DocPerm from Desk.
- Administrators can change Workflows from Desk.
- Workflow state names are not hard-coded in application logic.
- No hidden permission engine exists.

### Records

- Correspondence remains the authoritative record.
- Referral remains standalone.
- Connections expose the relationship.
- Attachments remain part of Correspondence.
- Integrity sealing remains application-enforced.

### Work

- Referral describes directed work.
- ToDo describes personal work.
- My Work shows personal action.
- Department routing does not become authorization logic.

### Security

- Reports respect native permissions.
- Linked-document enrichment does not leak restricted fields.
- Delegation does not bypass native permissions.
- Sealed records cannot be modified outside the defined invariant rules.

### UX

- User can understand From/To immediately.
- User can reach Referral from Correspondence.
- User can reach Correspondence from Referral.
- My Work is the primary operational entry point.
- Administration is secondary to work.

---

# 27. Final Architectural Position

The project should **not** evolve into a large custom framework.

It should evolve into a thin, highly disciplined domain application on top of Frappe.

The ideal ratio is:

```text
Frappe/ERPNext Native Capability
            ████████████████████████

Murasalat Domain Logic
            ████████

Custom UI
            ███
```

The custom code should exist where Murasalat has a genuine domain invariant:

- correspondence integrity
- referral recipient consistency
- sealing
- audit snapshot
- operational projections
- domain-specific reporting

Everything else should remain configurable through Desk.

That is the architecture most consistent with the original project vision.

---

# 28. Next Expert Pass

The next pass should move from architecture to **field-level and code-level forensic review**.

It should produce a matrix for every DocType:

| DocType | Field | Current Purpose | Keep/Change/Delete | Native Alternative | Risk | Priority |
|---|---|---|---|---|---|---|

Then a second matrix:

| Current Python/JS | Why it exists | Native Frappe alternative | Keep? | Refactor? |
|---|---|---|---|---|

Then a third:

| Report | Data source | Permission model | Delegation | Performance | Recommendation |
|---|---|---|---|---|---|

That is the point where we can safely decide whether v0.28 should be a UX release, an architecture-hardening release, or both.

---

## Official references

1. Frappe Desk — https://docs.frappe.io/framework/user/en/desk
2. Frappe DocTypes — https://docs.frappe.io/framework/user/en/basics/doctypes
3. Frappe Actions and Links / Connections — https://docs.frappe.io/framework/user/en/basics/doctypes/actions-and-links
4. Frappe DocType Layout — https://docs.frappe.io/framework/doctypes/doctype-layout
5. ERPNext Assignment Rule — https://docs.frappe.io/erpnext/assignment-rule
6. ERPNext Workflow Actions — https://docs.frappe.io/erpnext/workflow-actions