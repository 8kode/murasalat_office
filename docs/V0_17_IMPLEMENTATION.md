# Murasalat Office v0.17.0

## Focus
This release turns existing referral and correspondence data into manager-facing operational views without introducing a duplicate workflow engine.

## Added standard Frappe Script Reports
- Murasalat Overdue Referrals
- Murasalat Employee Productivity

## Design decisions
1. Reports query the canonical correspondence/referral records directly.
2. Overdue calculations are derived from referral due dates and open statuses.
3. Productivity is derived from referral receipt/completion timestamps.
4. No KPI DocType or parallel analytics database is introduced.
5. Overdue report reuses the correspondence permission query condition.

## Validation required on target bench
- bench --site <site> migrate
- bench --site <site> execute frappe.get_doc --args ... (smoke tests)
- Open both reports with User, Manager, and Auditor roles.
- Confirm confidentiality permission filtering for the overdue report.
