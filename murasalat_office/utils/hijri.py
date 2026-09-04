from __future__ import annotations

from hijridate import Gregorian

from frappe.utils import getdate


def gregorian_to_hijri(value) -> str | None:
	"""
	Convert a Gregorian date to an Umm al-Qura Hijri date.

	Return format:
	    YYYY-MM-DD

	Return None when value is empty.
	"""
	if not value:
		return None

	date_value = getdate(value)

	hijri_date = Gregorian(
		date_value.year,
		date_value.month,
		date_value.day,
	).to_hijri()

	return (
		f"{hijri_date.year:04d}-"
		f"{hijri_date.month:02d}-"
		f"{hijri_date.day:02d}"
	)


def current_hijri_year(value=None) -> int:
	"""
	Return the Hijri year for the supplied Gregorian date.
	When value is empty, today's date is used.
	"""
	date_value = getdate(value)
	hijri_date = Gregorian(
		date_value.year,
		date_value.month,
		date_value.day,
	).to_hijri()

	return hijri_date.year