"""Bring a migrated referral's recipient type into the vocabulary the DocType now declares.

``recipient_type`` began as a Select offering ``User`` / ``Organization`` and was later renamed
to ``User`` / ``Department`` while referrals were still child rows of a correspondence. The
conversion patch (``v0_21``) moved those rows into standalone documents and carried their values
across verbatim, so a row converted from the old vocabulary kept ``Organization`` - a value the
field no longer offers. Nothing refused it at the time, because nothing re-validated a migrated
row; the refusal surfaced later, on the first lifecycle action that ran the DocType's own
invariants: receiving the referral.

The target is derived from what the record actually links to before the old name is consulted,
because the link is the stronger evidence: a row naming a user and no department is a user
referral whatever its type field once said.

Read-only under ``dry_run``, idempotent, and it reports every row it could not resolve rather
than guessing a recipient for it.

    bench --site <site> execute murasalat_office.patches.v0_27_legacy_referral_vocabulary.execute
    bench --site <site> execute murasalat_office.patches.v0_27_legacy_referral_vocabulary.plan
"""
import frappe

DOCTYPE = "Murasalat Referral"
VALID = ("User", "Department")

# The names this field has carried. Anything else is reported, not guessed.
LEGACY = {
    "user": "User",
    "department": "Department",
    "dept": "Department",
    "organization": "Department",
    "organisation": "Department",
    "org": "Department",
}


def target_for(row) -> str | None:
    """The recipient type a migrated row should carry, or None when it cannot be derived.

    The link decides first: a row that names exactly one of the two recipients has already
    answered the question, whatever the type field says.
    """
    user = row.get("recipient_user")
    department = row.get("recipient_department")

    if user and not department:
        return "User"
    if department and not user:
        return "Department"

    return LEGACY.get((row.get("recipient_type") or "").strip().lower())


def rows_to_fix():
    """Every referral whose recipient type is outside the vocabulary the field declares."""
    return frappe.get_all(
        DOCTYPE,
        filters={"recipient_type": ["not in", list(VALID)]},
        fields=["name", "recipient_type", "recipient_user", "recipient_department"],
        limit_page_length=0,
    )


def plan():
    """Read-only: what would change, and what cannot be derived."""
    fixable, unresolved = [], []

    for row in rows_to_fix():
        target = target_for(row)
        if target:
            fixable.append({"name": row["name"], "from": row["recipient_type"], "to": target})
        else:
            unresolved.append({"name": row["name"], "recipient_type": row["recipient_type"]})

    print(f"{len(fixable)} referral(s) can be brought into the vocabulary")
    for entry in fixable:
        print(f"  {entry['name']}: {entry['from']!r} -> {entry['to']}")

    if unresolved:
        print(f"{len(unresolved)} cannot be derived - set the recipient type on each:")
        for entry in unresolved:
            print(f"  {entry['name']}: {entry['recipient_type']!r}")

    return {"fixable": fixable, "unresolved": unresolved}


def execute():
    """Apply the vocabulary. Idempotent: a row already in it is not touched again."""
    if not frappe.db.exists("DocType", DOCTYPE):
        return

    fixed, unresolved = 0, 0

    for row in rows_to_fix():
        target = target_for(row)

        if not target:
            unresolved += 1
            continue

        # update_modified=False: this repairs a stored vocabulary, it is not an edit to the
        # record, and a migrated row must not look freshly touched in the audit trail.
        frappe.db.set_value(DOCTYPE, row["name"], "recipient_type", target, update_modified=False)
        fixed += 1

    print(f"{fixed} referral(s) moved into the recipient vocabulary")
    if unresolved:
        print(f"{unresolved} left as they are - the recipient type could not be derived")
