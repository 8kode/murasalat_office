from __future__ import annotations

from datetime import date, datetime

import frappe
from frappe import _
from frappe.utils import getdate
from hijridate import Gregorian


def gregorian_to_hijri(value) -> str | None:
    if not value:
        return None

    try:
        gregorian_date = getdate(value)

        hijri_date = Gregorian(
            gregorian_date.year,
            gregorian_date.month,
            gregorian_date.day,
        ).to_hijri()

        return (
            f"{hijri_date.year:04d}-"
            f"{hijri_date.month:02d}-"
            f"{hijri_date.day:02d}"
        )

    except (TypeError, ValueError, OverflowError) as error:
        frappe.log_error(
            title="Murasalat Hijri Date Conversion",
            message=frappe.get_traceback(),
        )

        frappe.throw(
            _("Unable to convert Gregorian date {0} to Hijri.").format(
                value
            )
        )


def get_hijri_year(value) -> int | None:
    hijri_date = gregorian_to_hijri(value)

    if not hijri_date:
        return None

    return int(hijri_date.split("-")[0])