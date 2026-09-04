from __future__ import annotations

import frappe
from frappe.utils import cint


def get_current_user_profile(user=None):
	"""
	Return the active Murasalat User Profile for the supplied user.

	The function supports both old and new field names, such as:
	    department / default_department
	    company / default_company
	    priority_level / default_priority
	    confidentiality_level / default_confidentiality

	Return:
	    frappe._dict when a profile exists.
	    None when no profile exists.
	"""
	user = user or frappe.session.user

	if not frappe.db.exists(
		"DocType",
		"Murasalat User Profile",
	):
		return None

	meta = frappe.get_meta("Murasalat User Profile")

	if meta.issingle:
		return get_single_profile(meta, user)

	return get_standard_profile(meta, user)


def get_single_profile(meta, user):
	profile_doc = frappe.get_cached_doc(
		"Murasalat User Profile"
	)

	configured_user = (
		profile_doc.get("user")
		or profile_doc.get("system_user")
		or profile_doc.get("user_id")
	)

	if configured_user and configured_user != user:
		return None

	if (
		meta.has_field("is_active")
		and not cint(profile_doc.get("is_active"))
	):
		return None

	if (
		meta.has_field("enabled")
		and not cint(profile_doc.get("enabled"))
	):
		return None

	profile = frappe._dict(profile_doc.as_dict())

	return add_compatibility_aliases(profile)


def get_standard_profile(meta, user):
	user_field = find_first_existing_field(
		meta,
		(
			"user",
			"system_user",
			"user_id",
		),
	)

	if not user_field:
		return None

	filters = {
		user_field: user,
	}

	if meta.has_field("is_active"):
		filters["is_active"] = 1

	elif meta.has_field("enabled"):
		filters["enabled"] = 1

	fields = [
		"name",
		user_field,
	]

	optional_fields = (
		"employee",
		"department",
		"default_department",
		"company",
		"default_company",
		"confidentiality_level",
		"default_confidentiality",
		"priority_level",
		"default_priority",
	)

	for fieldname in optional_fields:
		if (
			meta.has_field(fieldname)
			and fieldname not in fields
		):
			fields.append(fieldname)

	profile = frappe.db.get_value(
		"Murasalat User Profile",
		filters,
		fields,
		as_dict=True,
	)

	if not profile:
		return None

	return add_compatibility_aliases(profile)


def find_first_existing_field(meta, fieldnames):
	for fieldname in fieldnames:
		if meta.has_field(fieldname):
			return fieldname

	return None


def add_compatibility_aliases(profile):
	"""
	Make old and new profile field names available to callers.
	"""
	profile = frappe._dict(profile)

	profile.department = (
		profile.get("department")
		or profile.get("default_department")
	)

	profile.default_department = (
		profile.get("default_department")
		or profile.get("department")
	)

	profile.company = (
		profile.get("company")
		or profile.get("default_company")
	)

	profile.default_company = (
		profile.get("default_company")
		or profile.get("company")
	)

	profile.confidentiality_level = (
		profile.get("confidentiality_level")
		or profile.get("default_confidentiality")
	)

	profile.default_confidentiality = (
		profile.get("default_confidentiality")
		or profile.get("confidentiality_level")
	)

	profile.priority_level = (
		profile.get("priority_level")
		or profile.get("default_priority")
	)

	profile.default_priority = (
		profile.get("default_priority")
		or profile.get("priority_level")
	)

	return profile
