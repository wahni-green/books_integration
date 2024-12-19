# Copyright (c) 2024, Wahni IT Solutions and contributors
# For license information, please see license.txt

import frappe
import json
from frappe.model.document import Document
from books_integration.scheduler import process_data


class BooksErrorLog(Document):
	@frappe.whitelist()
	def retry_processing(self):
		data = json.loads(self.data)
		process_data(
			self.books_instance, data, self.document_type
		)
		frappe.msgprint("Processed")
		self.delete()
