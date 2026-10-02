# Murasalat Office — Attachments

`Murasalat Attachment Type` and `Murasalat Archive Location` are native master DocTypes. Their permissions are site governance, not application fixtures.

Before users create or edit correspondence attachments, the System Manager should grant the required **Read** permission through **Role Permission Manager**.

Frappe `File` remains the canonical file object. Murasalat Attachment stores business metadata and the record index.
