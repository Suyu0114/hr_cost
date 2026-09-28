# Copyright (c) 2026, Suyu Cheng and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase

from hr_cost.hr_cost.doctype.employee.test_employee import make_employee

EXTRA_TEST_RECORD_DEPENDENCIES = []
IGNORE_TEST_RECORD_DEPENDENCIES = []

WORK_DATE = "2000-02-01"


def make_work_record(employee: str, hours_worked: float, date: str = WORK_DATE, **extra):
	return frappe.get_doc(
		{
			"doctype": "Work Record",
			"employee": employee,
			"hours_worked": hours_worked,
			"date": date,
			**extra,
		}
	).insert()


class IntegrationTestWorkRecord(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		self.alice = make_employee("Alice Wang", 20)
		self.bob = make_employee("Bob Lin", 35.5)

	def tearDown(self):
		frappe.db.rollback()
		super().tearDown()

	def test_cost_is_hours_times_rate(self):
		record = make_work_record(self.alice.name, 7.5)
		self.assertEqual(record.hourly_rate, 20)
		self.assertEqual(record.cost, 150)

	def test_employee_name_is_fetched(self):
		record = make_work_record(self.bob.name, 1)
		self.assertEqual(record.employee_name, "Bob Lin")

	def test_values_sent_by_client_are_recalculated(self):
		record = make_work_record(self.alice.name, 2, hourly_rate=999, cost=999)
		self.assertEqual(record.hourly_rate, 20)
		self.assertEqual(record.cost, 40)

	def test_rate_cannot_be_overwritten_on_update(self):
		# read_only is not enforced for REST updates, which call doc.update() + save().
		record = make_work_record(self.alice.name, 2)
		record.update({"hourly_rate": 999, "cost": 999})
		record.save()
		self.assertEqual(record.hourly_rate, 20)
		self.assertEqual(record.cost, 40)

	def test_rate_change_does_not_rewrite_existing_records(self):
		record = make_work_record(self.alice.name, 8)

		self.alice.hourly_rate = 30
		self.alice.save()

		# Editing hours later keeps the rate that applied when the work was logged.
		record.reload()
		record.hours_worked = 6
		record.save()
		self.assertEqual(record.hourly_rate, 20)
		self.assertEqual(record.cost, 120)

		# New records pick up the new rate.
		new_record = make_work_record(self.alice.name, 1, date="2000-02-02")
		self.assertEqual(new_record.hourly_rate, 30)

	def test_changing_employee_takes_the_new_employees_rate(self):
		record = make_work_record(self.alice.name, 4)
		record.employee = self.bob.name
		record.save()
		self.assertEqual(record.hourly_rate, 35.5)
		self.assertEqual(record.cost, 142)
		self.assertEqual(record.employee_name, "Bob Lin")

	def test_rejects_out_of_range_hours(self):
		for hours in (-1, 0, 24.5):
			with self.subTest(hours=hours), self.assertRaises(frappe.ValidationError):
				make_work_record(self.alice.name, hours)

	def test_rejects_more_than_24_hours_per_employee_per_day(self):
		make_work_record(self.alice.name, 16)
		with self.assertRaises(frappe.ValidationError):
			make_work_record(self.alice.name, 9)

		# Exactly 24 is fine, and a different employee or day is unaffected.
		second = make_work_record(self.alice.name, 8)
		make_work_record(self.bob.name, 24)
		make_work_record(self.alice.name, 24, date="2000-02-02")

		# Re-saving an existing record must not count its own hours twice.
		second.reload()
		second.save()

	def test_requires_existing_employee(self):
		with self.assertRaises(frappe.LinkValidationError):
			make_work_record("EMP-DOES-NOT-EXIST", 1)
