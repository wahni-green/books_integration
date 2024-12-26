# Copyright (c) 2024, Wahni IT Solutions and contributors
# For license information, please see license.txt

import frappe
from books_integration import __version__ as app_version


@frappe.whitelist(methods=["GET"])
def sync_settings():
    return {
        "success": True,
        "app_version": app_version,
        "data": frappe.get_cached_doc("Books Sync Settings").generate_sync_params()
    }


@frappe.whitelist(methods=["POST"])
def register_instance(instance, instance_name=None):
    if not instance:
        return {"success": False, "message": "Instance name is required"}

    if frappe.db.exists("Books Instance", instance):
        return {"success": False, "message": "Instance already registered"}

    frappe.get_doc({
        "doctype": "Books Instance",
        "device_id": instance,
        "instance_name": instance_name or instance
    }).insert(ignore_permissions=True)

    return {"success": True, "message": "Instance registered successfully"}
