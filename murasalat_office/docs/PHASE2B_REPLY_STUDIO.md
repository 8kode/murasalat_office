# Phase 2B — Reply Studio / Workflow Independent

## Architecture

- The incoming and outgoing record remain `Murasalat Correspondence`.
- `Murasalat Correspondence Link` with `relationship_type = Reply To` is the single source of truth.
- No Response DocType and no `reply_to_correspondence` field are introduced.
- Reply creation uses a native Frappe Dialog and a server-side service.
- The resulting outgoing correspondence has its own independent native Workflow.
- `Murasalat Referral` has its own independent native Workflow.
- The application never assumes state names such as Draft, Sent, Received, Completed, Closed or Sealed.
- Lifecycle services use business evidence fields (`registered_on`, `sent_on`, `received_on`, `completed_on`, `cancelled_on`, `closed_on`, `record_sealed_on`).

## Reply Studio

The dialog captures the official-letter information visible in the reference system:

- Reply To
- recipient
- preparation department
- subject
- salutation
- body
- closing phrase
- signatory name
- signatory position
- approval entity
- preparation entity
- preparation date

The dialog creates only an **Outgoing draft**. It does not approve, register, close, seal, or send the reply. Those actions belong to the institution's native Workflow.

## Print

`Murasalat Official Reply` is a native Jinja Print Format. The organization can use its own Letter Head and printing configuration.

## Security

The client button is only a convenience. The server re-checks read permission, `create_reply`, normal create permission, incoming direction, registration, closure/seal facts, sender/recipient facts, and open referrals.

## Native references

- Frappe Dialog API
- Frappe Form Scripts
- Frappe Permission Types v16
- Frappe Query Builder / permission-aware queries
- Frappe Print Formats
