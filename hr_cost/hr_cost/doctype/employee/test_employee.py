# Copyright (c) 2026, Suyu Cheng and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase

EXTRA_TEST_RECORD_DEPENDENCIES = []
IGNORE_TEST_RECORD_DEPENDENCIES = []


def make_employee(employee_name: str, hourly_rate: float):
	return frappe.get_doc(
		{"doctype": "Employee", "employee_name": employee_name, "hourly_rate": hourly_rate}
	).insert()


class IntegrationTestEmployee(IntegrationTestCase):
	def tearDown(self):
		# IntegrationTestCase only rolls back once per class; isolate every test.
		frappe.db.rollback()
		super().tearDown()

	def test_creates_employee_with_series_name(self):
		employee = make_employee("Alice Wang", 20)
		self.assertTrue(employee.name.startswith("EMP-"))
		self.assertEqual(employee.hourly_rate, 20)

	def test_strips_whitespace_from_name(self):
		employee = make_employee("  Bob Lin  ", 25)
		self.assertEqual(employee.employee_name, "Bob Lin")

	def test_rejects_zero_hourly_rate(self):
		with self.assertRaises(frappe.ValidationError):
			make_employee("Zero Rate", 0)

	def test_rejects_negative_hourly_rate(self):
		with self.assertRaises(frappe.ValidationError):
			make_employee("Negative Rate", -5)

	def test_rejects_blank_name(self):
		with self.assertRaises(frappe.ValidationError):
			make_employee("   ", 20)

	def test_cannot_delete_employee_with_work_records(self):
		employee = make_employee("Has Records", 20)
		frappe.get_doc(
			{"doctype": "Work Record", "employee": employee.name, "date": "2000-02-01", "hours_worked": 1}
		).insert()
		with self.assertRaises(frappe.LinkExistsError):
			frappe.delete_doc("Employee", employee.name)
