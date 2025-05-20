# Copyright (c) 2025, Wahni IT Solutions and contributors
# For license information, please see license.txt

import frappe
from frappe.model.naming import getseries

def autoname(doc, method=None):
    doc.name = getseries("POS Item Naming", 5)