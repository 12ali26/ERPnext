from __future__ import annotations

import random
from datetime import timedelta

import frappe
from frappe.utils import add_days, nowdate


def _field(doctype: str, fieldname: str) -> bool:
	return bool(frappe.get_meta(doctype).get_field(fieldname))


def _set(doc, fieldname: str, value):
	if _field(doc.doctype, fieldname):
		doc.set(fieldname, value)


def _exists(doctype: str, name: str) -> bool:
	return bool(frappe.db.exists(doctype, name))


def _insert(doc):
	doc.flags.ignore_permissions = True
	return doc.insert(ignore_permissions=True)


def _ensure_doc(doctype: str, name_field: str, name: str, values: dict | None = None):
	if _exists(doctype, name):
		return frappe.get_doc(doctype, name)

	doc = frappe.new_doc(doctype)
	doc.set(name_field, name)
	for fieldname, value in (values or {}).items():
		_set(doc, fieldname, value)
	return _insert(doc)


def _default_company() -> str:
	company = frappe.defaults.get_global_default("company")
	if company and _exists("Company", company):
		return company

	return frappe.db.get_value("Company", {}, "name")


def _company_abbr(company: str) -> str:
	return frappe.db.get_value("Company", company, "abbr")


def _ensure_uom(uom: str):
	return _ensure_doc("UOM", "uom_name", uom)


def _ensure_territory(name: str, parent: str = "All Territories", is_group: int = 0):
	return _ensure_doc(
		"Territory",
		"territory_name",
		name,
		{"parent_territory": parent, "is_group": is_group},
	)


def _ensure_item_group(name: str, parent: str = "All Item Groups"):
	return _ensure_doc(
		"Item Group",
		"item_group_name",
		name,
		{"parent_item_group": parent, "is_group": 0},
	)


def _ensure_warehouse(name: str, company: str):
	abbr = _company_abbr(company)
	full_name = f"{name} - {abbr}"
	if _exists("Warehouse", full_name):
		return frappe.get_doc("Warehouse", full_name)

	doc = frappe.new_doc("Warehouse")
	doc.warehouse_name = name
	doc.company = company
	doc.parent_warehouse = f"All Warehouses - {abbr}"
	_set(doc, "is_group", 0)
	return _insert(doc)


def _ensure_customer(name: str, territory: str, group: str, customer_type: str = "Company"):
	if _exists("Customer", name):
		return frappe.get_doc("Customer", name)

	doc = frappe.new_doc("Customer")
	doc.customer_name = name
	doc.customer_group = group
	doc.customer_type = customer_type
	doc.territory = territory
	return _insert(doc)


def _ensure_supplier(name: str, group: str):
	if _exists("Supplier", name):
		return frappe.get_doc("Supplier", name)

	doc = frappe.new_doc("Supplier")
	doc.supplier_name = name
	doc.supplier_group = group
	doc.supplier_type = "Company"
	return _insert(doc)


def _ensure_item(code: str, name: str, group: str, uom: str, category: str, batch: bool = False):
	if _exists("Item", code):
		return frappe.get_doc("Item", code)

	brand = "Ocean53" if category == "Paints" else "Pepsi" if category == "FMCG" else "Tallspan"
	_ensure_doc("Brand", "brand", brand)

	doc = frappe.new_doc("Item")
	doc.item_code = code
	doc.item_name = name
	doc.item_group = group
	doc.stock_uom = uom
	doc.is_stock_item = 1
	doc.include_item_in_manufacturing = 0
	_set(doc, "brand", brand)
	if batch:
		_set(doc, "has_batch_no", 1)
		_set(doc, "create_new_batch", 1)
		_set(doc, "shelf_life_in_days", 180 if category == "FMCG" else 365)
	return _insert(doc)


def _ensure_opportunity(customer: str, idx: int):
	name = f"CRM-{idx:03d}-{customer[:18]}"
	if _exists("Opportunity", name):
		return

	doc = frappe.new_doc("Opportunity")
	doc.naming_series = "CRM-.###"
	doc.title = name
	doc.opportunity_from = "Customer"
	doc.party_name = customer
	doc.status = random.choice(["Open", "Replied", "Quotation"])
	_set(doc, "opportunity_type", "Sales")
	_insert(doc)


def _ensure_sales_order(company: str, customer: str, warehouse: str, items: list[dict], idx: int):
	po_no = f"TALLSPAN-TRIAL-SO-{idx:03d}"
	if frappe.db.exists("Sales Order", {"po_no": po_no}):
		return

	doc = frappe.new_doc("Sales Order")
	doc.company = company
	doc.customer = customer
	doc.transaction_date = add_days(nowdate(), -random.randint(1, 20))
	doc.delivery_date = add_days(doc.transaction_date, random.randint(1, 5))
	doc.po_no = po_no
	doc.po_date = doc.transaction_date
	for row in items:
		doc.append(
			"items",
			{
				"item_code": row["item_code"],
				"qty": row["qty"],
				"rate": row["rate"],
				"delivery_date": doc.delivery_date,
				"warehouse": warehouse,
			},
		)
	_insert(doc)


@frappe.whitelist()
def seed_tallspan_trial():
	"""Seed Tallspan-style distribution data for the current trial site."""
	random.seed(42)
	company = _default_company()
	if not company:
		frappe.throw("Create a Company before seeding demo data.")

	for uom in ["Case", "Bag", "Kg", "Litre", "Tin"]:
		_ensure_uom(uom)

	_ensure_territory("Kenya", is_group=1)
	for territory in ["Mombasa", "Kilifi", "Kwale", "Malindi", "Diani", "Voi", "Lamu"]:
		_ensure_territory(territory, "Kenya")

	for group in ["FMCG - Soda", "Paints", "Cereals"]:
		_ensure_item_group(group)

	for warehouse in [
		"Tallspan Mombasa Main Warehouse",
		"Paint Safety Zone",
		"Expiry Hold Bay",
		"Truck MSA-001",
		"Truck MSA-002",
		"Truck KLF-003",
	]:
		_ensure_warehouse(warehouse, company)
	main_warehouse = _ensure_warehouse("Tallspan Mombasa Main Warehouse", company).name

	customers = [
		("Nyali Supermarket", "Mombasa", "Commercial"),
		("Likoni Mini Mart", "Mombasa", "Commercial"),
		("Bamburi Retailers", "Mombasa", "Commercial"),
		("Kilifi Wholesalers", "Kilifi", "Commercial"),
		("Malindi Beach Stores", "Malindi", "Commercial"),
		("Diani Hardware & Paints", "Diani", "Commercial"),
		("Kwale Cereals Depot", "Kwale", "Commercial"),
		("Voi Roadside Supplies", "Voi", "Commercial"),
		("Lamu Island Traders", "Lamu", "Commercial"),
		("Mtwapa Beverage Point", "Kilifi", "Commercial"),
	]
	for customer in customers:
		_ensure_customer(*customer)

	for supplier in [
		("Pepsi Coastal Distributor", "Distributor"),
		("Ocean53 Paint Factory", "Distributor"),
		("Tana River Cereal Millers", "Raw Material"),
		("Athi Grain Suppliers", "Raw Material"),
	]:
		_ensure_supplier(*supplier)

	items = [
		("PEPSI-300ML-CASE", "Pepsi Soda 300ml Returnable Case", "FMCG - Soda", "Case", "FMCG", 900),
		("MIRINDA-300ML-CASE", "Mirinda 300ml Returnable Case", "FMCG - Soda", "Case", "FMCG", 880),
		("7UP-500ML-CASE", "7UP 500ml PET Case", "FMCG - Soda", "Case", "FMCG", 1200),
		("O53-INT-4L-WHITE", "Ocean53 Interior Emulsion 4L Brilliant White", "Paints", "Tin", "Paints", 1450),
		("O53-EXT-20L-CREAM", "Ocean53 Exterior Paint 20L Coastal Cream", "Paints", "Tin", "Paints", 6200),
		("O53-GLOSS-1L-BLUE", "Ocean53 Gloss 1L Ocean Blue", "Paints", "Tin", "Paints", 720),
		("MAIZE-90KG-BAG", "Grade 1 Maize 90kg Bag", "Cereals", "Bag", "Cereals", 5200),
		("RICE-PISHORI-25KG", "Pishori Rice 25kg Bag", "Cereals", "Bag", "Cereals", 4300),
		("BEANS-ROSECoco-50KG", "Rosecoco Beans 50kg Bag", "Cereals", "Bag", "Cereals", 6800),
	]
	for code, name, group, uom, category, _rate in items:
		_ensure_item(code, name, group, uom, category, batch=category in {"FMCG", "Cereals"})

	customer_names = [customer[0] for customer in customers]
	item_rates = {code: rate for code, _name, _group, _uom, _category, rate in items}
	item_codes = list(item_rates)
	for idx, customer in enumerate(customer_names, start=1):
		_ensure_opportunity(customer, idx)
		order_items = []
		for code in random.sample(item_codes, 3):
			order_items.append({"item_code": code, "qty": random.randint(2, 12), "rate": item_rates[code]})
		_ensure_sales_order(company, customer, main_warehouse, order_items, idx)

	frappe.db.commit()
	return {
		"company": company,
		"customers": len(customers),
		"suppliers": 4,
		"items": len(items),
		"warehouses": 6,
		"sales_orders": len(customer_names),
		"opportunities": len(customer_names),
	}
