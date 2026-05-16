import frappe
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

	def before_submit(self):
		self.status = "Loaded"

	def on_cancel(self):
		self.status = "Cancelled"
