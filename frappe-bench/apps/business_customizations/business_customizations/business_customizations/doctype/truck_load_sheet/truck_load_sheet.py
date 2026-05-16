import frappe
from frappe import _
from frappe.model.document import Document


class TruckLoadSheet(Document):
	def validate(self):
		self.total_items = len(self.items or [])
		self.total_loaded_qty = sum(item.loaded_qty or 0 for item in self.items or [])

		for item in self.items or []:
			if item.loaded_qty and item.loaded_qty < 0:
				frappe.throw(f"Loaded Qty cannot be negative for row {item.idx}.")

			if not item.uom and item.item_code:
				item.uom = frappe.db.get_value("Item", item.item_code, "stock_uom")

			if not item.item_name and item.item_code:
				item.item_name = frappe.db.get_value("Item", item.item_code, "item_name")

		if self.source_warehouse and self.target_truck_warehouse:
			if self.source_warehouse == self.target_truck_warehouse:
				frappe.throw(_("Source Warehouse and Truck Warehouse cannot be the same."))

	def before_submit(self):
		self.status = "Loaded"

	def on_cancel(self):
		self.status = "Cancelled"

	@frappe.whitelist()
	def create_stock_entry(self):
		self.check_permission("write")

		if self.stock_entry:
			return self.stock_entry

		if not self.items:
			frappe.throw(_("Add loaded items before creating a Stock Entry."))

		stock_entry = frappe.new_doc("Stock Entry")
		stock_entry.company = self.company
		stock_entry.stock_entry_type = "Material Transfer"
		stock_entry.purpose = "Material Transfer"
		stock_entry.from_warehouse = self.source_warehouse
		stock_entry.to_warehouse = self.target_truck_warehouse
		stock_entry.posting_date = self.posting_date
		stock_entry.set_posting_time = 1
		stock_entry.remarks = _("Created from Truck Load Sheet {0}").format(self.name)

		for item in self.items:
			if not item.loaded_qty or item.loaded_qty <= 0:
				continue

			stock_entry.append(
				"items",
				{
					"item_code": item.item_code,
					"qty": item.loaded_qty,
					"s_warehouse": self.source_warehouse,
					"t_warehouse": self.target_truck_warehouse,
					"uom": item.uom,
					"stock_uom": item.uom,
					"conversion_factor": 1,
					"transfer_qty": item.loaded_qty,
					"batch_no": item.batch_no,
					"allow_zero_valuation_rate": 1,
				},
			)

		if not stock_entry.items:
			frappe.throw(_("At least one loaded item must have a quantity greater than zero."))

		stock_entry.insert(ignore_permissions=True)
		self.db_set("stock_entry", stock_entry.name)
		return stock_entry.name
