# Copyright (c) 2024, Wahni IT Solutions and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import create_batch
from books_integration.doc_converter import DocConverter
from books_integration.utils import get_doctype_name, save_document_name, pretty_json


@frappe.whitelist(methods=["GET"])
def get_pending_docs(instance):
    queued_docs = frappe.db.get_all(
        "Books Sync Queue",
        filters={"books_instance": instance},
        fields=["name", "document_type", "document_name"]
    )

    if not queued_docs:
        return {"success": True, "data": []}

    docs = []
    for queued_doc in queued_docs:
        doc = frappe.get_doc(queued_doc.document_type, queued_doc.document_name)
        existing_books_ref = frappe.db.get_value(
            "Books Reference",
            {
                "document_type": queued_doc.doctype_name,
                "document_name": queued_doc.document_name,
            },
            "books_name"
        )
        doc_converter_obj = DocConverter(doc, "fbooks")
        compatable_doc = doc_converter_obj.get_converted_doc()

        if existing_books_ref:
            compatable_doc["fbooksDocName"] = existing_books_ref

        docs.append(compatable_doc)

    return {"success": True, "data": docs}


@frappe.whitelist(methods=["POST"])
def initiate_master_sync(instance, records):
    if not records:
        return {"success": False, "message": "No records found"}
    
    if not instance:
        return {"success": False, "message": "Books instance not found"}

    success_log = []
    failed_log = []

    for record in records:
        try:
            data = {
                "doctype": "Books Sync Queue",
                "document_type": get_doctype_name(
                    record.get("referenceType"), "erpn"
                ),
                "document_name": record.get("documentName"),
            }
            is_pending = frappe.db.exists(data)

            if not is_pending:
                frappe.get_doc(data).save()

            success_log.append(
                {
                    "document_name": record.get("documentName"),
                    "doctype_name": record.get("referenceType"),
                }
            )
        except Exception:
            frappe.log_error(
                title=f"Books Integration Error - {instance}",
                message=frappe.get_traceback(),
            )

            failed_log.append(
                {
                    "document_name": record.get("documentName"),
                    "doctype_name": record.get("referenceType"),
                }
            )

    return {"success": True, "success_log": success_log, "failed_log": failed_log}


@frappe.whitelist(methods=["POST"])
def sync_transactions(instance, transaction_type, records):
    batches = create_batch(records, 15)
    for batch in batches:
        doc = frappe.new_doc("Books Integration Log")
        doc.books_instance = instance
        doc.document_type = transaction_type
        doc.data = pretty_json(batch)
        doc.save(ignore_permissions=True)

    frappe.enqueue(
        "books_integration.scheduler.process_transactions",
        queue="long",
        enqueue_after_commit=True,
    )

    return {
        "success": True,
        "message": "Books Integration Log created successfully",
    }


@frappe.whitelist(methods=["POST"])
def update_status(instance, data):
    ref_data = {
        "doctype": "Books Sync Queue",
        "name": data.get("nameInERPNext"),
        "books_name": data.get("nameInFBooks"),
    }

    save_document_name(instance, ref_data)
    try:
        frappe.get_doc("Books Sync Queue", data.get("sync_id")).delete()
    except Exception:
        frappe.log_error(
            title=f"Books Integration Error - {instance} - Update Status",
            message=frappe.get_traceback(),
        )
        return {"success": False}

    return {"success": True}
