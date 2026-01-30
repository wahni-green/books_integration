# Copyright (c) 2024, Wahni IT Solutions and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import create_batch, today, strip_html_tags
from books_integration.doc_converter import init_doc_converter
from books_integration.utils import get_doctype_name, update_books_reference, pretty_json
from frappe.query_builder.functions import IfNull, Max

syncable_doc_types = [
    "Item Group",
    "UOM",
    "Batch",
    "Item",
    "Price List",
    "Pricing Rule",
]


@frappe.whitelist(methods=["GET"])
def get_pending_docs(instance, doctype=None, all_docs=False):
    item_rates = get_item_rates()
    if not item_rates:
        return {
            "success": False,
            "message": "price list not selected in Books Sync Settings"
        }

    if all_docs:
        return get_all_docs_for_initial_sync(instance, item_rates)

    filters = {"books_instance": instance}
    if doctype:
        filters["document_type"] = doctype

    queued_docs = frappe.db.get_all(
        "Books Sync Queue",
        filters=filters,
        fields=["name", "document_type", "document_name", "books_instance"]
    )

    if not queued_docs:
        return {"success": True, "data": []}

    docs_by_type = {}
    for doc in queued_docs:
        docs_by_type.setdefault(doc.document_type, []).append(doc)

    ordered_docs = []
    for doc_type in syncable_doc_types:
        if doc_type in docs_by_type:
            ordered_docs.extend(docs_by_type[doc_type])

    for doc_type, docs in docs_by_type.items():
        if doc_type not in syncable_doc_types:
            ordered_docs.extend(docs)

    queued_docs = ordered_docs

    docs = []
    processed_pricelists = set()
    for queued_doc in queued_docs:
        try:
            doc = frappe.get_doc(
                queued_doc.document_type, queued_doc.document_name
            )
            existing_books_ref = frappe.db.get_value(
                "Books Reference",
                {
                    "document_type": queued_doc.document_type,
                    "document_name": queued_doc.document_name,
                    "books_instance": instance,
                },
                "books_name"
            )
            doc_converter_obj = init_doc_converter(
                queued_doc.books_instance, doc, "fbooks"
            )
            if not doc_converter_obj:
                continue
            compatable_doc = doc_converter_obj.get_converted_doc()

            if compatable_doc.get("description"):
                compatable_doc["description"] = strip_html_tags(compatable_doc["description"])

            if existing_books_ref:
                compatable_doc["fbooksDocName"] = existing_books_ref

            compatable_doc["books_sync_id"] = queued_doc.name
            if compatable_doc.get("doctype") == "Item":
                compatable_doc["rate"] = item_rates.get(compatable_doc.get("itemCode"), 0)

            if compatable_doc.get("doctype") == "PriceList":
                pricelist_name = compatable_doc.get("name")

                if pricelist_name in processed_pricelists:
                    continue

                processed_pricelists.add(pricelist_name)
                
                if compatable_doc.get("priceListItem"):
                    seen_items = set()
                    unique_items = []

                    for item in compatable_doc.get("priceListItem"):
                        item_key = (item.get("item"), item.get("unit"))

                        if item_key not in seen_items:
                            seen_items.add(item_key)
                            unique_items.append(item)

                    compatable_doc["priceListItem"] = unique_items

            docs.append(compatable_doc)
        except Exception as e:
            frappe.log_error(
                title=f"Books Integration Error - Processing {queued_doc.document_type} {queued_doc.document_name}",
                message=frappe.get_traceback(),
            )
            continue

    return {"success": True, "data": docs}


def get_all_docs_for_initial_sync(instance, item_rates):
    all_docs = []

    for doctype in syncable_doc_types:
        try:
            if doctype == "Party":
                for party_type in ["Customer", "Supplier"]:
                    all_docs.extend(
                        fetch_docs_by_type(party_type, instance, item_rates)
                    )
            else:
                all_docs.extend(
                    fetch_docs_by_type(doctype, instance, item_rates)
                )
        except Exception:
            frappe.log_error(
                title=f"Books Integration Error - Fetching {doctype} (Initial Sync)",
                message=frappe.get_traceback(),
            )
            continue

    return {"success": True, "data": all_docs}


def fetch_docs_by_type(doctype, instance, item_rates):
    docs = []

    try:
        doc_names = frappe.get_all(doctype, pluck='name')
        for doc_name in doc_names:
            try:
                doc = frappe.get_doc(doctype, doc_name)
                existing_books_ref = frappe.db.get_value(
                    "Books Reference",
                    {
                        "document_type": doctype,
                        "document_name": doc_name,
                        "books_instance": instance,
                    },
                    "books_name"
                )

                doc_converter_obj = init_doc_converter(instance, doc, "fbooks")
                if not doc_converter_obj:
                    continue

                compatable_doc = doc_converter_obj.get_converted_doc()
                if compatable_doc.get("description"):
                    compatable_doc["description"] = strip_html_tags(compatable_doc["description"])

                if existing_books_ref:
                    compatable_doc["fbooksDocName"] = existing_books_ref

                compatable_doc["books_sync_id"] = None 

                if compatable_doc.get("doctype") == "Item":
                    compatable_doc["rate"] = item_rates.get(compatable_doc.get("itemCode"), 0)

                docs.append(compatable_doc)

            except Exception as e:
                frappe.log_error(
                    title=f"Books Integration Error - Processing {doctype} {doc_name} (Initial Sync)",
                    message=frappe.get_traceback(),
                )
                continue

    except Exception as e:
        frappe.log_error(
            title=f"Books Integration Error - Fetching {doctype} list (Initial Sync)",
            message=frappe.get_traceback(),
        )

    return docs


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