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


def save_document_name(doctype: str, erpn_filename=str, fbooks_filename=str):
    doc_exists = frappe.db.exists(
        {
            "doctype": "Books ERPN Doc Name",
            "doctype_name": get_doctype_name(doctype, "erpn"),
            "name_in_erpnext": erpn_filename,
            "name_in_fbooks": fbooks_filename,
        }
    )

    if doc_exists:
        return

    frappe.get_doc(
        {
            "doctype": "Books ERPN Doc Name",
            "doctype_name": get_doctype_name(doctype, "erpn"),
            "name_in_erpnext": erpn_filename,
            "name_in_fbooks": fbooks_filename,
        }
    ).insert()


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
