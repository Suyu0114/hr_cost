# Copyright (c) 2026, Suyu Cheng and contributors
# For license information, please see license.txt

"""Daily HR Cost: total labour cost per day, with period totals.

Cost per Work Record is `hours_worked * hourly_rate`, where the rate is the one
snapshotted on the record when it was logged (see WorkRecord.set_hourly_rate).
"""

import frappe
from frappe import _
from frappe.utils import add_days, date_diff, flt, get_first_day, get_last_day, getdate, today

MAX_DAYS_WITH_EMPTY_ROWS = 366


def execute(filters: dict | None = None):
	filters = frappe._dict(filters or {})
	set_default_filters(filters)
	validate_filters(filters)

	records = get_employee_day_totals(filters)
	data = build_daily_rows(records, filters)

	return get_columns(), data, None, get_chart(data), get_report_summary(data, records)


def set_default_filters(filters: frappe._dict) -> None:
	"""Default to the current month when called without filters (e.g. via the API)."""
	filters.from_date = getdate(filters.from_date or get_first_day(today()))
	filters.to_date = getdate(filters.to_date or get_last_day(today()))


def validate_filters(filters: frappe._dict) -> None:
	if filters.from_date > filters.to_date:
		frappe.throw(_("From Date cannot be after To Date."), title=_("Invalid Date Range"))

	if (
		filters.include_empty_days
		and date_diff(filters.to_date, filters.from_date) >= MAX_DAYS_WITH_EMPTY_ROWS
	):
		frappe.throw(
			_("Showing days without work is limited to {0} days. Narrow the date range.").format(
				MAX_DAYS_WITH_EMPTY_ROWS
			),
			title=_("Date Range Too Long"),
		)


def get_columns() -> list[dict]:
	return [
		{"label": _("Date"), "fieldname": "date", "fieldtype": "Date", "width": 130},
		{"label": _("Employees"), "fieldname": "employees", "fieldtype": "Int", "width": 110},
		{"label": _("Total Hours"), "fieldname": "total_hours", "fieldtype": "Float", "width": 130},
		{"label": _("Total HR Cost"), "fieldname": "total_cost", "fieldtype": "Currency", "width": 160},
	]


def get_employee_day_totals(filters: frappe._dict) -> list[frappe._dict]:
	"""One row per (date, employee).

	`frappe.get_list` applies the current user's permissions, so a user who cannot
	read Work Records cannot see their costs through this report either.
	Grouping by employee as well as date lets us count distinct employees per day
	without raw SQL (the query builder's dict syntax has no COUNT DISTINCT).
	"""
	conditions = {"date": ["between", [filters.from_date, filters.to_date]]}
	if filters.employee:
		conditions["employee"] = filters.employee

	return frappe.get_list(
		"Work Record",
		filters=conditions,
		fields=[
			"date",
			"employee",
			{"SUM": "hours_worked", "as": "hours"},
			{"SUM": "cost", "as": "cost"},
		],
		group_by="date, employee",
		order_by="date asc",
		limit=0,  # 0 = no limit; never truncate a cost report
	)


def build_daily_rows(records: list[frappe._dict], filters: frappe._dict) -> list[dict]:
	hours_precision = frappe.get_precision("Work Record", "hours_worked")
	cost_precision = frappe.get_precision("Work Record", "cost")

	by_date: dict = {}
	for record in records:
		day = by_date.setdefault(
			getdate(record.date), {"employees": 0, "total_hours": 0.0, "total_cost": 0.0}
		)
		day["employees"] += 1
		day["total_hours"] += flt(record.hours)
		day["total_cost"] += flt(record.cost)

	if filters.include_empty_days:
		dates = [
			add_days(filters.from_date, i) for i in range(date_diff(filters.to_date, filters.from_date) + 1)
		]
	else:
		dates = sorted(by_date)

	rows = []
	for date in dates:
		day = by_date.get(getdate(date), {"employees": 0, "total_hours": 0.0, "total_cost": 0.0})
		rows.append(
			{
				"date": getdate(date),
				"employees": day["employees"],
				"total_hours": flt(day["total_hours"], hours_precision),
				"total_cost": flt(day["total_cost"], cost_precision),
			}
		)
	return rows


def get_chart(data: list[dict]) -> dict | None:
	if not data:
		return None

	# The chart truncates x-axis labels longer than ~3 characters to "..." when a whole
	# month of bars is shown, so use the day number within a single month, M/D otherwise.
	single_month = len({(row["date"].year, row["date"].month) for row in data}) == 1
	labels = [
		str(row["date"].day) if single_month else f"{row['date'].month}/{row['date'].day}" for row in data
	]

	return {
		"data": {
			"labels": labels,
			"datasets": [{"name": _("HR Cost"), "values": [row["total_cost"] for row in data]}],
		},
		"type": "bar",
		"fieldtype": "Currency",
	}


def get_report_summary(data: list[dict], records: list[frappe._dict]) -> list[dict]:
	"""Period totals shown above the table.

	We use summary cards instead of the report's "Add Total Row" option because
	Frappe's server-side total row sums every Int column, which would add up the
	daily head counts in exports (e.g. 3 + 2 + 3 = 8 "employees").
	"""
	cost_precision = frappe.get_precision("Work Record", "cost")
	hours_precision = frappe.get_precision("Work Record", "hours_worked")
	return [
		{
			"label": _("Total HR Cost"),
			"value": flt(sum(row["total_cost"] for row in data), cost_precision),
			"datatype": "Currency",
			"indicator": "Blue",
		},
		{
			"label": _("Total Hours"),
			"value": flt(sum(row["total_hours"] for row in data), hours_precision),
			"datatype": "Float",
		},
		{
			"label": _("Days With Work"),
			"value": sum(1 for row in data if row["employees"]),
			"datatype": "Int",
		},
		{
			"label": _("Employees"),
			"value": len({record.employee for record in records}),
			"datatype": "Int",
		},
	]
