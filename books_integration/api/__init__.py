# Copyright (c) 2024, Wahni IT Solutions and contributors
# For license information, please see license.txt

import frappe
from books_integration import __version__ as app_version


@frappe.whitelist(methods=["GET"])
def sync_settings():
    return {
        "success": True,
        "app_version": app_version,
        "data": frappe.get_cached_doc("Books Sync Settings")
    }
