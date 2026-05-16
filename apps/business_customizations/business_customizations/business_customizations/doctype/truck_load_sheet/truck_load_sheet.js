frappe.ui.form.on("Truck Load Sheet", {
	refresh(frm) {
		if (!frm.doc.__islocal && !frm.doc.stock_entry) {
			frm.add_custom_button(__("Create Stock Entry"), () => {
				frappe.call({
					doc: frm.doc,
					method: "create_stock_entry",
					freeze: true,
					freeze_message: __("Creating Stock Entry..."),
					callback(r) {
						if (!r.exc && r.message) {
							frm.reload_doc();
							frappe.set_route("Form", "Stock Entry", r.message);
						}
					},
				});
			});
		}

		if (frm.doc.stock_entry) {
			frm.add_custom_button(__("Open Stock Entry"), () => {
				frappe.set_route("Form", "Stock Entry", frm.doc.stock_entry);
			});
		}
	},
});
