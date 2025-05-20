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


@frappe.whitelist(methods=["POST"])
def register_instance(instance, instance_name=None):
    if not instance:
        return {"success": False, "message": "Instance name is required"}

    if frappe.db.exists("Books Instance", instance):
        return {"success": True, "message": "Instance already registered"}

    frappe.get_doc({
        "doctype": "Books Instance",
        "device_id": instance,
        "instance_name": instance_name or instance
    }).insert(ignore_permissions=True)

    message = {"success": True, "message": "Instance registered successfully"}
    books_sync_settings = frappe.get_single("Books Sync Settings")
    mappings = dict(
        tax_mapping = books_sync_settings.tax_mapping,
        mode_of_payment_mapping = books_sync_settings.mode_of_payment_mapping
    )
    if not mappings.get("mode_of_payment_mapping"):
        message = {
            "success": False,
            "message": "Mode of Payment Mapping Not Set in Books Sync Settings(ERPNext)"
        }
    if not mappings.get("tax_mapping"):
        message = {
            "success": False,
            "message": "Tax Mapping Not Set in Books Sync Settings(ERPNext)"
        }
    
    return message
