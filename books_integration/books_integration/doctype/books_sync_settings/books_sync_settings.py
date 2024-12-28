# Copyright (c) 2024, Wahni IT Solutions and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class BooksSyncSettings(Document):
	def generate_sync_params(self):
		data = self.as_dict()

		sync_params = {
			"Item": ["sync_item", "item_sync_type"],
			"Customer": ["sync_customer", "customer_sync_type"],
			"Supplier": ["sync_supplier", "supplier_sync_type"],
			"Sales Invoice": ["sync_sales_invoice", "sales_invoice_sync_type"],
			"Payment Entry": ["sync_payment_entry", "payment_entry_sync_type"],
			"Stock Entry": ["sync_stock_entry", "stock_sync_type"],
			"Price List": ["sync_price_list", "price_list_sync_type"],
			"Serial No": ["sync_serial_number", "serial_number_sync_type"],
			"Batch": ["sync_batches", "batch_sync_type"],
			"Delivery Note": ["sync_delivery_note", "delivery_note_sync_type"],
		}

		for (sync, sync_type) in sync_params.values():
			data[sync] = 0
			data[sync_type] = "Two Way"

		for row in self.sync_docs:
			param = sync_params.get(row.document_type)
			if not param:
				continue

			data[param[0]] = 1
			data[param[1]] = row.sync_type

		return data
