# Copyright (c) 2025, Wahni IT Solutions and contributors
# For license information, please see license.txt

from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    create_custom_fields(
        {
            "POS Opening Entry": [
                {
                    "fieldname": "from_frappebooks",
                    "label": "From FrappeBooks",
                    "fieldtype": "Check",
                    "insert_after": "period_end_date",
                    "read_only": 0,
                },
                {
                    "fieldname": "books_instance",
                    "label": "Books Instance",
                    "fieldtype": "Link",
                    "options": "Books Instance",
                    "insert_after": "from_frappebooks",
                    "read_only": 1,
                },
            ],
            "POS Closing Entry": [
                {
                    "fieldname": "from_frappebooks",
                    "label": "From FrappeBooks",
                    "fieldtype": "Check",
                    "insert_after": "period_end_date",
                    "read_only": 0,
                },
                {
                    "fieldname": "books_instance",
                    "label": "Books Instance",
                    "fieldtype": "Link",
                    "options": "Books Instance",
                    "insert_after": "from_frappebooks",
                    "read_only": 1,
                },
            ],
            "Sales Invoice": [
                {
                    "fieldname": "from_frappebooks",
                    "label": "From FrappeBooks",
                    "fieldtype": "Check",
                    "insert_after": "customer",
                    "read_only": 0,
                },
                {
                    "fieldname": "books_instance",
                    "label": "Books Instance",
                    "fieldtype": "Link",
                    "options": "Books Instance",
                    "insert_after": "from_frappebooks",
                    "read_only": 1,
                },
            ],
            "Payment Entry": [
                {
                    "fieldname": "from_frappebooks",
                    "label": "From FrappeBooks",
                    "fieldtype": "Check",
                    "insert_after": "payment_type",
                    "read_only": 0,
                },
                {
                    "fieldname": "books_instance",
                    "label": "Books Instance",
                    "fieldtype": "Link",
                    "options": "Books Instance",
                    "insert_after": "from_frappebooks",
                    "read_only": 1,
                },
            ]
        }
    )