# Murasalat Office — Workflow Governance

Murasalat does **not** ship or impose a Workflow state model. The institution creates its own native Frappe Workflow for `Murasalat Correspondence` and its own independent Workflow for `Murasalat Referral`.

The application exposes these optional native Workflow Transition Task methods:

- Register Correspondence
- Close Correspondence
- Seal Correspondence
- Reopen Correspondence
- Send Referral
- Receive Referral
- Complete Referral
- Cancel Referral
- Stamp Approval
- Clear Approval

Attach a task only to the transition where the institution wants that business action to occur. The task names do not define or constrain the Workflow state names.

## Transaction boundary

Transition Tasks that mutate the document must run synchronously. Do not enable **Asynchronous** for these lifecycle tasks: the methods update the in-memory document and rely on the transition transaction to persist the result.

The client UI is not the security boundary. Each server-side task validates permissions and business invariants again.
