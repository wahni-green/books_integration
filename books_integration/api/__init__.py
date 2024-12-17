# Copyright (c) 2024, Wahni IT Solutions and contributors
# For license information, please see license.txt


import frappe
import json
from books_integration.doc_converter import DocConverter
from books_integration.utils import get_doctype_name, update_books_reference


@frappe.whitelist(methods=["GET"])
def sync_settings():
    """
    Endpoint    : books_integration.api.sync_settings
    GET         : Returns the single Doctype, Books Sync Settings
    """
    sync_settings_doc = frappe.get_single("Books Sync Settings")
    version = frappe.utils.change_log.get_versions()["books_integration"]["version"]

    return {"success": True, "app_version": version, "data": sync_settings_doc}
