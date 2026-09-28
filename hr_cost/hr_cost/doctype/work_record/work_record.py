# Copyright (c) 2026, Suyu Cheng and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.query_builder.functions import Sum
from frappe.utils import flt, format_date

MAX_HOURS_PER_DAY = 24


class WorkRecord(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		cost: DF.Currency
		date: DF.Date
		employee: DF.Link
		employee_name: DF.Data | None
		hourly_rate: DF.Currency
		hours_worked: DF.Float
	# end: auto-generated types

	_DOCTYPE_NAME = "Work Record"

	def validate(self):
		self.validate_hours_worked()
		self.validate_daily_hours_limit()
		self.set_hourly_rate()
		self.set_cost()

	def validate_hours_worked(self):
		hours = flt(self.hours_worked)
		if hours <= 0 or hours > MAX_HOURS_PER_DAY:
			frappe.throw(
				_("Hours Worked must be greater than 0 and not more than {0}.").format(MAX_HOURS_PER_DAY),
				title=_("Invalid Hours Worked"),
			)

	def validate_daily_hours_limit(self):
		"""One employee cannot log more than 24 hours on the same date across all records."""
		work_record = frappe.qb.DocType("Work Record")
		logged_elsewhere = (
			frappe.qb.from_(work_record)
			.select(Sum(work_record.hours_worked))
			.where(
				(work_record.employee == self.employee)
				& (work_record.date == self.date)
				# `self.name` is always set by the time validate() runs, but guard against
				# NULL anyway: `name != NULL` would silently exclude every row.
				& (work_record.name != (self.name or ""))
			)
		).run()[0][0]

		total = flt(logged_elsewhere) + flt(self.hours_worked)
		if total > MAX_HOURS_PER_DAY:
			frappe.throw(
				_("{0} already has {1} hours logged on {2}. Adding {3} hours would exceed {4} hours.").format(
					frappe.bold(self.employee_name or self.employee),
					flt(logged_elsewhere),
					format_date(self.date),
					flt(self.hours_worked),
					MAX_HOURS_PER_DAY,
				),
				title=_("Daily Hours Exceeded"),
			)

	def set_hourly_rate(self):
		"""Snapshot the employee's rate so later rate changes do not rewrite past costs.

		The rate is copied from the Employee when the record is created or re-pointed to
		another employee. On any other save the stored snapshot is kept, whatever value
		the client sent: `read_only` is only enforced by the Desk form, not by the REST
		API. (A plain `fetch_from` would not work here either: Frappe re-fetches those
		fields on every save of a non-submitted document.)
		"""
		previous = self.get_doc_before_save()
		if previous and previous.employee == self.employee and previous.hourly_rate:
			self.hourly_rate = previous.hourly_rate
		else:
			self.hourly_rate = frappe.db.get_value("Employee", self.employee, "hourly_rate")

	def set_cost(self):
		self.cost = flt(flt(self.hours_worked) * flt(self.hourly_rate), self.precision("cost"))
