# Copyright (c) 2024, Wahni IT Solutions and contributors
# For license information, please see license.txt

import frappe


def add_doc_to_sync_queue(doc, method=None):
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
        is_exists_in_queue = frappe.db.exists(
            {
                "doctype": "Books Sync Queue",
                "document_name": doc.name,
                "document_type": doc.doctype,
                "books_instance": instance,
            }
        )
        if not is_exists_in_queue:
            frappe.get_doc(
                {
                    "doctype": "Books Sync Queue",
                    "document_name": doc.name,
                    "doctype_name": doc.doctype,
                    "books_instance": instance,
                }
            ).insert()


def document_should_sync(doctype):
    settings = frappe.get_cached_doc("Books Sync Settings")
    if not settings.enable_sync:
        return False

    if doctype == "Item Price":
        return settings.sync_price_list

    return settings.get("sync_{}".format(frappe.scrub(doctype)))