# Copyright (c) 2024, Wahni IT Solutions and contributors
# For license information, please see license.txt

import frappe


ERP_DOCTYPE_MAP = {
    "Item": "Item",
    "Customer": "Customer",
    "Supplier": "Supplier",
    "Sales Invoice": "SalesInvoice",
    "Payment Entry": "Payment",
    "Payment Entry Reference": "PaymentFor",
    "Stock Entry": "StockMovement",
    "Price List": "PriceList",
    "Item Price": "PriceListItem",
    "Serial No": "SerialNumber",
    "Batch": "Batch",
    "UOM": "UOM",
    "UOM Conversion Detail": "UOMConversionItem",
    "Delivery Note": "Shipment",
    "Address": "Address",
    "POS Opening Entry": "POSOpeningShift",
    "POS Closing Entry": "POSClosingShift",
    "Pricing Rule": "PricingRule",
    "Item Group": "ItemGroup",
}

BOOKS_DOCTYPE_MAP = {v: k for k, v in ERP_DOCTYPE_MAP.items()}


def get_doctype_name(doctype: str, target, doc=None):
    if not target:
        return

    if not doctype:
        if not doc.get("doctype"):
            return
        doctype = doc.get("doctype")

    if target == "erpn":
        if doc and doctype == "Party":
            return doc.get("role")
        return BOOKS_DOCTYPE_MAP.get(doctype)

    return ERP_DOCTYPE_MAP.get(doctype)


def update_books_reference(instance, reference):
    doctype = get_doctype_name(
        reference.get("doctype"), "erpn"
    )
    existing_ref = frappe.db.get_value(
        "Books Reference",
        {
            "document_type": doctype,
            "document_name": reference.get("doc").get("itemCode") if doctype == "Item" else reference.get("name"),
            "books_instance": instance,
        },
        ["books_name", "name"],
        as_dict=True,
    )

    if not existing_ref:
        frappe.get_doc(
            {
                "doctype": "Books Reference",
                "document_type": doctype,
                "document_name": reference.get("doc").get("itemCode") if doctype == "Item" else reference.get("name"),
                "books_instance": instance,
                "books_name": reference.get("books_name"),
            },
        ).insert()
        return

    if existing_ref.books_name == reference.get("books_name"):
        return

    if existing_ref.books_name != reference.get("books_name"):
        frappe.db.set_value(
            "Books Reference", existing_ref.name, "books_name", reference.get("books_name")
        )

    return


def pretty_json(obj):
    if not obj:
        return ""

    if isinstance(obj, str):
        return obj

    return frappe.as_json(obj, indent=4)
