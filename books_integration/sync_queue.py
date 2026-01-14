# Copyright (c) 2024, Wahni IT Solutions and contributors
# For license information, please see license.txt

import frappe


def add_doc_to_sync_queue(doc, method=None):
    if frappe.flags.in_books_process:
        return

    if doc.meta.is_submittable and doc.docstatus == 0:
        return

    if not document_should_sync(doc.doctype):
        return

    instances = frappe.db.get_all(
        "Books Instance",
        # filters={"enable_sync": 1},
        pluck="name",
    )
    for instance in instances:
        add_to_queue_if_not_exists(
            doc.doctype, doc.name, instance)

        if doc.doctype == "Item":
            add_item_related_docs(doc, instance)

def add_item_related_docs(doc, instance):
    item_batches = frappe.db.get_all("Batch", {"item": doc.name}, "name")
    for batch in item_batches:
        add_to_queue_if_not_exists("Batch", batch.get("name"), instance)

    if doc.item_group:
        add_to_queue_if_not_exists("Item Group", doc.item_group, instance)

    price_lists_with_item = frappe.db.sql("""
        SELECT DISTINCT ip.price_list
        FROM `tabItem Price` ip
        WHERE ip.item_code = %s
    """, (doc.name,), as_dict=True)
    
    for price_list in price_lists_with_item:
        add_to_queue_if_not_exists("Price List", price_list.get("price_list"), instance)


def add_to_queue_if_not_exists(doctype, docname, instance):
    if not frappe.db.exists(
        {
            "doctype": "Books Sync Queue",
            "document_name": docname,
            "document_type": doctype,
            "books_instance": instance,
        }
    ):
        frappe.get_doc(
            {
                "doctype": "Books Sync Queue",
                "document_name": docname,
                "document_type": doctype,
                "books_instance": instance,
            }
        ).insert()


def document_should_sync(doctype):
    settings = frappe.get_cached_doc("Books Sync Settings")
    if not settings.enable_sync:
        return False

    if doctype == "Item Price":
        doctype = ["Price List"]
    elif doctype == "Mode of Payment":
        doctype = ["Sales Invoice", "Payment Entry"]
    else:
        doctype = [doctype]

    # for row in settings.sync_docs:
    #     if row.document_type in doctype:
    #         return True
    return True

    # return False

def add_item(doc, method=None):
    # runs when item price is modified
    if not should_sync_item_price(doc):
        return
        
    instances = frappe.db.get_all(
        "Books Instance",
        # filters={"enable_sync": 1},
        pluck="name",
    )
    for instance in instances:
        is_item_exists = frappe.db.exists(
            {
                "doctype": "Books Sync Queue",
                "document_name": doc.item_code,
                "document_type": "Item",
                "books_instance": instance,
            }
        )
        if not is_item_exists:
            frappe.get_doc(
                {
                    "doctype": "Books Sync Queue",
                    "document_name": doc.item_code,
                    "document_type": "Item",
                    "books_instance": instance,
                }
            ).insert()

        if doc.price_list:
            is_pricelist_exists = frappe.db.exists(
                {
                    "doctype": "Books Sync Queue",
                    "document_name": doc.price_list,
                    "document_type": "Price List",
                    "books_instance": instance,
                }
            )
            if not is_pricelist_exists:
                frappe.get_doc(
                    {
                        "doctype": "Books Sync Queue",
                        "document_name": doc.price_list,
                        "document_type": "Price List",
                        "books_instance": instance,
                    }
                ).insert()


def should_sync_item_price(doc):
    """
    Check if Item Price data actually changed and needs syncing.
    Only sync when meaningful price data changes, not on system updates.
    """
    if doc.is_new():
        return True
    
    old_doc = doc.get_doc_before_save()
    if not old_doc:
        return True
    
    price_related_fields = [
        'price_list_rate', 'item_code', 'uom', 'price_list', 'valid_from', 'valid_upto'
    ]
    
    for field in price_related_fields:
        old_value = old_doc.get(field)
        new_value = doc.get(field)
        
        if (old_value or new_value) and old_value != new_value:
            frappe.logger().debug(f"Item Price {doc.name}: {field} changed from '{old_value}' to '{new_value}', triggering sync")
            return True
    
    frappe.logger().debug(f"Item Price {doc.name}: No meaningful changes detected, skipping sync")
    return False


def sync_existing_items(instance):
    all_items = frappe.db.get_all("Item")
    for item in all_items:
        is_exists_in_queue = frappe.db.exists(
            {
                "doctype": "Books Sync Queue",
                "document_name": item.item_code,
                "document_type": "Item",
                "books_instance": instance,
            }
        )
        if not is_exists_in_queue:
            frappe.get_doc(
                {
                    "doctype": "Books Sync Queue",
                    "document_name": item.item_code,
                    "document_type": "Item",
                    "books_instance": instance,
                }
            ).insert()