# Copyright (c) 2026, Suyu Cheng and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class Employee(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		employee_name: DF.Data
		hourly_rate: DF.Currency
	# end: auto-generated types

	_DOCTYPE_NAME = "Employee"

	def validate(self):
		self.employee_name = (self.employee_name or "").strip()
		if not self.employee_name:
			frappe.throw(_("Employee Name is required."), title=_("Missing Employee Name"))

		# Rejects negatives as well as zero: a zero rate is almost always a data-entry
		# mistake and would silently zero out HR cost. (The field's `non_negative`
		# flag is only checked after validate(), so this is the check that fires.)
		if flt(self.hourly_rate) <= 0:
			frappe.throw(_("Hourly Rate must be greater than 0."), title=_("Invalid Hourly Rate"))
