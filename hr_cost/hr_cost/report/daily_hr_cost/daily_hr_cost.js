// Copyright (c) 2026, Suyu Cheng and contributors
// For license information, please see license.txt

frappe.query_reports["Daily HR Cost"] = {
	filters: [
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.month_start(),
			reqd: 1,
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.month_end(),
			reqd: 1,
		},
		{
			fieldname: "employee",
			label: __("Employee"),
			fieldtype: "Link",
			options: "Employee",
		},
		{
			fieldname: "include_empty_days",
			label: __("Include Days Without Work"),
			fieldtype: "Check",
			default: 0,
		},
	],
};
