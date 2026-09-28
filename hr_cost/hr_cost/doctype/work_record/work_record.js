// Copyright (c) 2026, Suyu Cheng and contributors
// For license information, please see license.txt

// Live preview only: the server recalculates hourly_rate and cost on save
// (see work_record.py), so these values are never trusted from the browser.
frappe.ui.form.on("Work Record", {
	employee(frm) {
		if (!frm.doc.employee) {
			frm.set_value("hourly_rate", 0);
			return;
		}
		frappe.db.get_value("Employee", frm.doc.employee, "hourly_rate").then((r) => {
			frm.set_value("hourly_rate", r.message ? r.message.hourly_rate : 0);
		});
	},

	hours_worked(frm) {
		frm.trigger("calculate_cost");
	},

	hourly_rate(frm) {
		frm.trigger("calculate_cost");
	},

	calculate_cost(frm) {
		frm.set_value("cost", flt(frm.doc.hours_worked) * flt(frm.doc.hourly_rate));
	},
});
