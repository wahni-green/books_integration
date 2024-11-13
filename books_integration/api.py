import frappe
import json
from books_integration.doc_converter import DocConverter
from .utils import get_doctype_name, save_document_name


@frappe.whitelist(methods=["GET"])
def sync_settings():
    """
    Endpoint    : books_integration.api.sync_settings
    GET         : Returns the single Doctype, Books Sync Settings
    """
    sync_settings_doc = frappe.get_single("Books Sync Settings")
    version = frappe.utils.change_log.get_versions()["books_integration"]["version"]

    return {"success": True, "app_version": version, "data": sync_settings_doc}


@frappe.whitelist(methods=["GET", "POST"])
def sync_queue():
    """
    Endpoint    : books_integration.api.sync_queue
    GET         : Returns the Documents in the Sync Queue
    POST        : Adds a Document to the Sync Queue
    """

    if frappe.request.method == "GET":
        docs = list()
        queued_docs = frappe.db.get_all(
            "Sync Queue", fields=["name", "doctype_name", "document_name"]
        )

        if len(queued_docs) < 1:
            return {"success": True}

        for queued_doc in queued_docs:
            doc = frappe.get_doc(queued_doc.doctype_name, queued_doc.document_name)
            is_doc_synced_before = frappe.db.exists(
                {
                    "doctype": "Books ERPN Doc Name",
                    "doctype_name": queued_doc.doctype_name,
                    "name_in_erpnext": queued_doc.document_name,
                }
            )
            doc_converter_obj = DocConverter(doc, "fbooks")
            compatable_doc = doc_converter_obj.get_converted_doc()

            if is_doc_synced_before:
                fbooks_doc_name = frappe.get_doc(
                    "Books ERPN Doc Name", is_doc_synced_before
                )

                compatable_doc["fbooksDocName"] = fbooks_doc_name.get("name_in_fbooks")

            docs.append(compatable_doc)

        return {"success": True, "data": docs}

    else:
        if not frappe.request.data:
            return {"success": False}

        data = json.loads(frappe.request.data)
        records = data.get("records")

        if not records:
            return {"success": False}

        success_log = list()
        failed_log = list()

        for record in records:
            try:
                is_exists = frappe.db.exists(
                    {
                        "doctype": "Sync Queue",
                        "doctype_name": get_doctype_name(
                            record.get("referenceType"), "erpn"
                        ),
                        "document_name": record.get("documentName"),
                    }
                )

                if is_exists:
                    success_log.append(
                        {
                            "document_name": record.get("documentName"),
                            "doctype_name": record.get("referenceType"),
                        }
                    )
                    continue

                frappe.get_doc(
                    {
                        "doctype": "Sync Queue",
                        "doctype_name": get_doctype_name(
                            record.get("referenceType"), "erpn"
                        ),
                        "document_name": record.get("documentName"),
                    }
                ).save()

                success_log.append(
                    {
                        "document_name": record.get("documentName"),
                        "doctype_name": record.get("referenceType"),
                    }
                )

            except:
                failed_log.append(
                    {
                        "document_name": record.get("documentName"),
                        "doctype_name": record.get("referenceType"),
                    }
                )

        return {"success": True, "success_log": success_log, "failed_log": failed_log}


@frappe.whitelist(methods=["POST"])
def insert_docs():
    """
    Endpoint    : books_integration.api.insert_docs
    POST        : Syncs an Books Document to Frappe
    """
    data = json.loads(frappe.request.data)
    payload = data.get("payload")
    success_log = list()
    failed_log = list()

    if not payload or not data:
        return {"success": False}

    for data in payload:
        converted_doc = DocConverter(data, "erpn")
        erpn_compatable_doc = converted_doc.get_converted_doc()

        try:
            is_doc_exists = frappe.db.exists(
                {
                    "doctype": "Books ERPN Doc Name",
                    "doctype_name": get_doctype_name(data.get("doctype"), "erpn"),
                    "name_in_fbooks": data.get("name"),
                }
            )

            if is_doc_exists:
                existing_doc_name = frappe.db.get_value(
                    "Books ERPN Doc Name", is_doc_exists, "name_in_erpnext"
                )

                existing_doc = frappe.get_doc(
                    get_doctype_name(data.get("doctype"), "erpn"), existing_doc_name
                )

                existing_doc.update(erpn_compatable_doc)
                existing_doc.save()

                if data.get("submitted"):
                    existing_doc.run_method("submit")

                if data.get("cancelled"):
                    existing_doc.run_method("cancel")

            else:
                new_doc = converted_doc.get_frappe_doc()


                converted_doc.run_doc_method("before_save")
                new_doc.insert()
                converted_doc.run_doc_method("after_save")

                if data.get("submitted"):
                    new_doc.run_method("submit")
                    converted_doc.run_doc_method("after_submit")

                if data.get("cancelled"):
                    new_doc.run_method("cancel")
                    converted_doc.run_doc_method("after_cancel")

                save_document_name(
                    data.get("doctype"),
                    new_doc.get("name"),
                    data.get("name"),
                )

            success_log.append(
                {"name": data.get("name"), "doctype": data.get("doctype")}
            )

        except Exception as e:
            failed_log.append(
                {"name": data.get("name"), "doctype": data.get("doctype"), "e": e}
            )

    return {"success": True, "success_log": success_log, "failed_log": failed_log}


@frappe.whitelist(methods=["POST"])
def perform_aftersync():
    """
    Endpoint    : books_integration.api.perform_aftersync
    POST        :
                Removes the Synced Document from the Sync Queue,
                Saves the equivalent document name in Books to handle document updates easily.
    """

    data = json.loads(frappe.request.data)

    if not data:
        return {"success": False}

    is_doc_exists_in_queue = frappe.db.exists(
        {
            "doctype": "Sync Queue",
            "doctype_name": get_doctype_name(
                data.get("doctype"), "erpn", data.get("doc", data)
            ),
            "document_name": data.get("nameInERPNext"),
        }
    )

    if not is_doc_exists_in_queue:
        save_document_name(
            data.get("doctype"), data.get("nameInERPNext"), data.get("nameInFBooks")
        )

    frappe.get_doc("Sync Queue", is_doc_exists_in_queue).delete()
    return {"success": True}
