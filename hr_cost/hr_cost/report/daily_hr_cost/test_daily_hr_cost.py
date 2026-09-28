# Copyright (c) 2026, Suyu Cheng and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import getdate

from hr_cost.hr_cost.doctype.employee.test_employee import make_employee
from hr_cost.hr_cost.doctype.work_record.test_work_record import make_work_record
from hr_cost.hr_cost.report.daily_hr_cost.daily_hr_cost import execute

# A date range no real data will use, so the expected totals are exact.
FROM_DATE, TO_DATE = "2000-02-01", "2000-02-03"


class TestDailyHRCost(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		self.alice = make_employee("Alice Wang", 20)
		self.bob = make_employee("Bob Lin", 35.5)

		# Feb 1: Alice 8h + 1h (split shift) = 9h x 20 = 180; Bob 4h x 35.5 = 142 -> 322
		make_work_record(self.alice.name, 8, "2000-02-01")
		make_work_record(self.alice.name, 1, "2000-02-01")
		make_work_record(self.bob.name, 4, "2000-02-01")
		# Feb 2: nobody worked
		# Feb 3: Bob 8h x 35.5 = 284
		make_work_record(self.bob.name, 8, "2000-02-03")
		# Outside the range: must be ignored
		make_work_record(self.alice.name, 5, "2000-02-04")

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()
		super().tearDown()

	def run_report(self, **filters):
		columns, data, _message, chart, summary = execute(
			{"from_date": FROM_DATE, "to_date": TO_DATE, **filters}
		)
		return columns, data, chart, {card["label"]: card["value"] for card in summary}

	def test_daily_totals(self):
		_columns, data, _chart, summary = self.run_report()
		self.assertEqual(
			data,
			[
				{"date": getdate("2000-02-01"), "employees": 2, "total_hours": 13, "total_cost": 322},
				{"date": getdate("2000-02-03"), "employees": 1, "total_hours": 8, "total_cost": 284},
			],
		)
		self.assertEqual(
			summary,
			{"Total HR Cost": 606, "Total Hours": 21, "Days With Work": 2, "Employees": 2},
		)

	def test_include_days_without_work(self):
		_columns, data, chart, summary = self.run_report(include_empty_days=1)
		self.assertEqual([row["total_cost"] for row in data], [322, 0, 284])
		self.assertEqual(chart["data"]["datasets"][0]["values"], [322, 0, 284])
		self.assertEqual(chart["data"]["labels"], ["1", "2", "3"])
		self.assertEqual(summary["Days With Work"], 2)

	def test_chart_labels_across_months(self):
		make_work_record(self.alice.name, 2, "2000-01-31")
		_columns, _data, chart, _summary = self.run_report(from_date="2000-01-31")
		self.assertEqual(chart["data"]["labels"], ["1/31", "2/1", "2/3"])

	def test_employee_filter(self):
		_columns, data, _chart, summary = self.run_report(employee=self.bob.name)
		self.assertEqual([row["total_cost"] for row in data], [142, 284])
		self.assertEqual(summary["Total HR Cost"], 426)
		self.assertEqual(summary["Employees"], 1)

	def test_uses_the_rate_snapshot_not_the_current_rate(self):
		self.alice.hourly_rate = 100
		self.alice.save()
		_columns, data, _chart, _summary = self.run_report()
		self.assertEqual(data[0]["total_cost"], 322)

	def test_empty_range(self):
		_columns, data, chart, summary = self.run_report(from_date="1999-01-01", to_date="1999-01-31")
		self.assertEqual(data, [])
		self.assertIsNone(chart)
		self.assertEqual(summary["Total HR Cost"], 0)

	def test_rejects_reversed_date_range(self):
		with self.assertRaises(frappe.ValidationError):
			execute({"from_date": TO_DATE, "to_date": FROM_DATE})

	def test_user_without_access_cannot_read_costs(self):
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": "hr-cost-no-access@example.com",
				"first_name": "No Access",
				"send_welcome_email": 0,
			}
		).insert(ignore_permissions=True)
		frappe.set_user(user.name)
		with self.assertRaises(frappe.PermissionError):
			execute({"from_date": FROM_DATE, "to_date": TO_DATE})
