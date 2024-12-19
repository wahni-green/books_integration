// Copyright (c) 2024, Wahni IT Solutions and contributors
// For license information, please see license.txt

frappe.ui.form.on("Books Error Log", {
	refresh(frm) {
        frm.add_custom_button(__("Retry"), function () {
            frm.call("retry_processing");
        });
	},
});
