import frappe
import datetime


def get_doctype_name(doctype: str, target, doc=None):
    if target == "erpn":
        if doc and doctype == "Party":
            return doc.get("role")

        doctype_name_idx = list(doctype_map.values()).index(doctype)
        return list(doctype_map.keys())[doctype_name_idx]

    else:
        if not doctype and not doc.get("doctype"):
            return

        doctype_name_idx = list(doctype_map.keys()).index(doctype)
        return list(doctype_map.values())[doctype_name_idx]


def update_books_reference(instance, reference):
    doctype = get_doctype_name(
        reference.get("doctype"), "erpn"
    )
    existing_ref = frappe.db.get_value(
        {
            "doctype": "Books Reference",
            "document_type": doctype,
            "document_name": reference.get("name"),
            "instance": instance,
        },
        ["books_name", "name"],
        as_dict=True,
    )

    if not existing_ref:
        frappe.get_doc(
            {
                "doctype": "Books Reference",
                "document_type": doctype,
                "document_name": reference.get("name"),
                "instance": instance,
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



doctype_map = {
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
    "Address": "Address"
}


def convert_date_for_frappe(input_date):
    input_datetime = datetime.datetime.fromisoformat(input_date)
    output_str = input_datetime.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

    return output_str


def pretty_json(obj):
    if not obj:
        return ""

    if isinstance(obj, str):
        return obj

    return frappe.as_json(obj, indent=4)