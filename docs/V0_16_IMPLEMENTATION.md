# v0.16.0 – Operational State Machine & SLA Hardening

## Focus
This release hardens the operational layer without replacing native Frappe Workflow, ToDo, Timeline, Version or role permissions.

## Changes
- One server-side transition registry defines legal referral state transitions.
- Terminal referrals cannot be transitioned again.
- Referral receive/start/complete/reject/return operations record a canonical operational activity.
- Closing checks unresolved referrals server-side.
- Reopening is auditable and resets only the operational closure marker.
- Daily escalation now processes due/overdue events safely and only emits manager/final escalation after the configured threshold.
- A read-only operational summary API exposes current holder, open/overdue referral counts and nearest due date for dashboards or Workspace shortcuts.

## Frappe-first principle
The release intentionally uses native DocType history, child tables, ToDo, Notification Log, scheduler events, permissions and Workflow instead of introducing a parallel workflow engine.
