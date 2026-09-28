# Copyright (c) 2026, Suyu Cheng and contributors
# For license information, please see license.txt

import frappe


def has_app_permission() -> bool:
	"""Show the HR Cost tile on the apps screen only to users who can read its data."""
	return bool(frappe.has_permission("Work Record", "read") or frappe.has_permission("Employee", "read"))
