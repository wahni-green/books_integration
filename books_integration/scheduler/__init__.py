# Copyright (c) 2024, Wahni IT Solutions and contributors
# For license information, please see license.txt

import frappe
import json
from books_integration.doc_converter import init_doc_converter
from books_integration.utils import get_doctype_name, update_books_reference, pretty_json


def enqueue_process_transactions():
    frappe.enqueue(
        "books_integration.scheduler.process_transactions",
        queue="long",
        enqueue_after_commit=True,
        job_id="BOOKS_SYNC_TRANSACTION_JOB",
        deduplicate=True
    )


def process_transactions():
    log = frappe.db.get_value(
        "Books Integration Log",
        {"processed": 0},
        ["name", "data", "books_instance"],
        as_dict=True
    )
    if not log:
        return

    frappe.db.set_value("Books Integration Log", log.name, "processed", 1)
    data = json.loads(log.data)
    primary_doctypes = ["SalesInvoice", "POSOpeningShift", "ItemGroup"]
    primary_docs = [row for row in data if row.get("doctype") in primary_doctypes]
    secondary_docs = [row for row in data if row.get("doctype") not in primary_doctypes]
    frappe.flags.in_books_process = True
    for record in primary_docs+secondary_docs:
        try:
            doctype = get_doctype_name(record.get("doctype"), "erpn")
            process_data(log.books_instance, record, doctype)
        except Exception:
            frappe.get_doc({
                "doctype": "Books Error Log",
                "error": frappe.get_traceback(),
                "data": pretty_json(record),
                "document_type": doctype,
                "books_instance": log.books_instance,
                "books_integration_log": log.name
            }).insert(ignore_permissions=True)

    frappe.flags.in_books_process = False


def process_data(instance, data, doctype):
    conv_doc = init_doc_converter(instance, data, "erpn")
    if not conv_doc:
        return

    ref_exists = frappe.db.get_value(
        "Books Reference",
        {
            "document_type": doctype,
            "books_name": data.get("name"),
            "books_instance": instance
        },
        "document_name"
    )

    if not ref_exists:
        create_record(
            conv_doc,
            data.get("name"),
            data.get("submitted"),
            data.get("cancelled"),
            data.get("doctype"),
            instance
        )
        return

    _doc = frappe.get_doc(doctype, ref_exists)
    _doc.update(conv_doc.get_converted_doc())
    _doc.flags.ignore_permissions = True
    _doc.run_method("set_missing_values")
    _doc.save()

    if (
        data.get("submitted")
        and _doc.meta.is_submittable
    ):
        _doc.submit()

    if (
        data.get("cancelled")
        and _doc.docstatus == 1
    ):
        _doc.cancel()


def create_record(
    _doc, ref, submit, cancel, doctype, instance
):
    doc = _doc.get_frappe_doc()
    doc.flags.ignore_permissions = True
    doc.run_method("set_missing_values")
    doc.insert()
    other_docs = ["POS Opening Entry", "POS Closing Entry"]

    if doc.doctype in other_docs:
        doc.submit()

    if submit and doc.meta.is_submittable:
        doc.submit()

    if cancel and doc.docstatus == 1:
        doc.cancel()

    reference = {
        "doctype": doctype,
        "name": doc.name,
        "books_name": ref
    }
    update_books_reference(instance, reference)
