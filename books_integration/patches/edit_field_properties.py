# Copyright (c) 2025, Wahni IT Solutions and contributors
# For license information, please see license.txt

import frappe

def execute():
    property_list = [
        {
            "doctype": "Item",
            "fieldname": "stock_uom",
            "property": "default",
            "value":"Unit"
        },
    ]

    for property in property_list:
        frappe.make_property_setter(property)