import frappe


def add_doc_to_sync_queue(doc, method):
    if not document_should_sync(doc):
        return

    is_exists_in_queue = frappe.db.exists(
        {
            "doctype": "Books Sync Queue",
            "document_name": doc.name,
            "doctype_name": doc.doctype,
        }
    )
    if not is_exists_in_queue:
        frappe.get_doc(
            {
                "doctype": "Books Sync Queue",
                "document_name": doc.name,
                "doctype_name": doc.doctype,
            }
        ).insert()


def document_should_sync(doc):
    doctype = doc.doctype
    
    is_sync_enabled = frappe.db.get_single_value("Books Sync Settings", "enable_sync")

    if doctype == "Item Price":
        is_sync_enabled_for_price_list = frappe.db.get_single_value(
            "Books Sync Settings", "sync_price_list"
        )

        return is_sync_enabled and is_sync_enabled_for_price_list

    formatted_doctype_name = "_".join(doctype.lower().split(" "))
    is_sync_enabled_for_doctype = frappe.db.get_single_value(
        "Books Sync Settings", "sync_{}".format(formatted_doctype_name)
    )

    return is_sync_enabled and is_sync_enabled_for_doctype
