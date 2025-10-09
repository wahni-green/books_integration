# Copyright (c) 2024, Wahni IT Solutions and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import create_batch, today
from books_integration.doc_converter import init_doc_converter
from books_integration.utils import get_doctype_name, update_books_reference, pretty_json
from frappe.query_builder.functions import IfNull, Max


@frappe.whitelist(methods=["GET"])
def get_pending_docs(instance):
    item_rates = get_item_rates()
    if not item_rates:
        return {
            "success": False,
            "message": "price list not selected in Books Sync Settings"
        }
    queued_docs = frappe.db.get_all(
        "Books Sync Queue",
        filters={"books_instance": instance},
        fields=["name", "document_type", "document_name", "books_instance"]
    )

    if not queued_docs:
        return {"success": True, "data": []}

    docs = []
    for queued_doc in queued_docs:
        doc = frappe.get_doc(
            queued_doc.document_type, queued_doc.document_name
        )
        existing_books_ref = frappe.db.get_value(
            "Books Reference",
            {
                "document_type": queued_doc.document_type,
                "document_name": queued_doc.document_name,
            },
            "books_name"
        )
        doc_converter_obj = init_doc_converter(
            queued_doc.books_instance, doc, "fbooks"
        )
        if not doc_converter_obj:
            continue
        compatable_doc = doc_converter_obj.get_converted_doc()

        if existing_books_ref:
            compatable_doc["fbooksDocName"] = existing_books_ref

        compatable_doc["books_sync_id"] = queued_doc.name
        if compatable_doc.get("doctype") == "Item":
            compatable_doc["rate"] = item_rates.get(compatable_doc.get("itemCode"), 0)
            item_group_name = frappe.db.get_value("Item", doc.name, "item_group")
            if item_group_name:
                if not frappe.db.exists("Books Reference", {
                    "document_type": "Item Group",
                    "document_name": item_group_name,
                    "books_instance": instance
                }):
                    item_group_doc = frappe.get_doc("Item Group", item_group_name)
                    item_group_converter = init_doc_converter(
                        queued_doc.books_instance, item_group_doc, "fbooks"
                    )
                    if item_group_converter:
                        item_group_compatable = item_group_converter.get_converted_doc()
                        item_group_compatable["books_sync_id"] = queued_doc.name
                        docs.append(item_group_compatable)

        elif compatable_doc.get("doctype") == "Batch":
            batch_item = frappe.db.get_value("Batch", doc.name, "item")
            if batch_item:

                if not frappe.db.exists("Books Reference", {
                    "document_type": "Item",
                    "document_name": batch_item,
                    "books_instance": instance
                }):
                    item_doc = frappe.get_doc("Item", batch_item)
                    item_converter = init_doc_converter(
                        queued_doc.books_instance, item_doc, "fbooks"
                    )
                    if item_converter:
                        item_compatable = item_converter.get_converted_doc()
                        item_compatable["books_sync_id"] = queued_doc.name
                        item_compatable["rate"] = item_rates.get(item_compatable.get("itemCode"), 0)
                        docs.append(item_compatable)

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
def sync_transactions(instance, records):
    settings = frappe.get_doc("Books Sync Settings")
    if not settings.get("mode_of_payment_mapping"):
        return {
        "success": False,
        "message": "Please Set Mode of Payment Mapping in Books Sync Settings",
    }
    batches = create_batch(records, 15)
    for batch in batches:
        doc = frappe.new_doc("Books Integration Log")
        doc.books_instance = instance
        doc.data = pretty_json(batch)
        doc.save(ignore_permissions=True)

    frappe.enqueue(
        "books_integration.scheduler.process_transactions",
        queue="long",
        enqueue_after_commit=True,
        job_id="BOOKS_SYNC_TRANSACTION_JOB",
        deduplicate=True
    )

    return {
        "success": True,
        "message": "Books Integration Log created successfully",
    }


@frappe.whitelist(methods=["POST"])
def update_status(instance, data):
    ref_data = {
        "doctype": data.get("doctype"),
        "name": data.get("nameInERPNext"),
        "books_name": data.get("nameInFBooks"),
        "doc": data.get("doc"),
    }

    update_books_reference(instance, ref_data)
    try:
        frappe.get_doc("Books Sync Queue", data.get('doc').get("books_sync_id")).delete()
    except Exception:
        frappe.log_error(
            title=f"Books Integration Error - {instance} - Update Status",
            message=frappe.get_traceback(),
        )
        return {"success": False}

    return {"success": True}

def get_item_rates():
    price_list = frappe.db.get_single_value("Books Sync Settings", "price_list")
    if not price_list:
        return None
    item_price = frappe.qb.DocType("Item Price")

    ip_subquery = (
        frappe.qb.from_(item_price)
        .select(
            item_price.item_code,
            Max(item_price.valid_from).as_("valid_from"),
        )
        .where(item_price.price_list == price_list)
        .where(IfNull(item_price.valid_from, "2000-01-01") <= today())
        .groupby(item_price.item_code)
        .as_("ip_subquery")
    )
    item_rates = (
        frappe.qb.from_(item_price)
        .inner_join(ip_subquery)
        .on(
            (item_price.item_code == ip_subquery.item_code)
            & (item_price.valid_from == ip_subquery.valid_from)
        )
        .select(
            item_price.item_code,
            item_price.price_list_rate,
        )
        .where(item_price.price_list == price_list)
        .run()
    )
    return dict(item_rates) or {}