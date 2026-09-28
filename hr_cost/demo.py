# Copyright (c) 2026, Suyu Cheng and contributors
# For license information, please see license.txt

"""Optional demo data so the report has something to show.

    bench --site <site> execute hr_cost.demo.make_demo_data

Creates three employees and weekday Work Records for the current month up to
today. Safe to run twice: it does nothing if the demo employees already exist.
"""

import frappe
from frappe.utils import add_days, get_first_day, getdate, today

DEMO_EMPLOYEES = {
	"Alice Wang": 20,
	"Bob Lin": 35.5,
	"Carol Chen": 28,
}


def make_demo_data():
	if frappe.db.exists("Employee", {"employee_name": ["in", list(DEMO_EMPLOYEES)]}):
		print("Demo employees already exist; nothing to do.")
		return

	employees = {
		name: frappe.get_doc({"doctype": "Employee", "employee_name": name, "hourly_rate": rate})
		.insert()
		.name
		for name, rate in DEMO_EMPLOYEES.items()
	}

	day, last_day, created = getdate(get_first_day(today())), getdate(today()), 0
	while day <= last_day:
		weekday = day.weekday()  # Monday = 0
		if weekday < 5:
			shifts = {"Alice Wang": 8, "Carol Chen": 4 if weekday == 4 else 7.5}
			if weekday in (0, 2, 4):
				shifts["Bob Lin"] = 6
			for name, hours in shifts.items():
				frappe.get_doc(
					{
						"doctype": "Work Record",
						"employee": employees[name],
						"date": day,
						"hours_worked": hours,
					}
				).insert()
				created += 1
		day = getdate(add_days(day, 1))

	frappe.db.commit()
	print(f"Created {len(employees)} employees and {created} work records.")
