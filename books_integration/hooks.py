app_name = "books_integration"
app_title = "Books Integration"
app_publisher = "Wahni IT Solutions"
app_description = "Frappe Books Integration for ERPNext"
app_email = "akshay@wahni.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "books_integration",
# 		"logo": "/assets/books_integration/logo.png",
# 		"title": "Books Integration",
# 		"route": "/books_integration",
# 		"has_permission": "books_integration.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/books_integration/css/books_integration.css"
# app_include_js = "/assets/books_integration/js/books_integration.js"

# include js, css files in header of web template
# web_include_css = "/assets/books_integration/css/books_integration.css"
# web_include_js = "/assets/books_integration/js/books_integration.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "books_integration/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "books_integration/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "books_integration.utils.jinja_methods",
# 	"filters": "books_integration.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "books_integration.install.before_install"
# after_install = "books_integration.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "books_integration.uninstall.before_uninstall"
# after_uninstall = "books_integration.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "books_integration.utils.before_app_install"
# after_app_install = "books_integration.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "books_integration.utils.before_app_uninstall"
# after_app_uninstall = "books_integration.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "books_integration.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
    (
        "Item", "Customer", "Supplier", 
        "Stock Entry", "Price List", "Item Price",
        "Serial No", "Batch", "Delivery Note"
    ): {
        "on_update": "books_integration.sync_queue.add_doc_to_sync_queue",
    },
}

# Scheduled Tasks
# ---------------

scheduler_events = {
	"hourly": [
		"books_integration.scheduler.enqueue_process_transactions"
	],
}

# Testing
# -------

# before_tests = "books_integration.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "books_integration.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "books_integration.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["books_integration.utils.before_request"]
# after_request = ["books_integration.utils.after_request"]

# Job Events
# ----------
# before_job = ["books_integration.utils.before_job"]
# after_job = ["books_integration.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"books_integration.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }
