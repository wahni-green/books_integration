# Copyright (c) 2024, Wahni IT Solutions and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt, getdate
from books_integration.utils import get_doctype_name


class DocConverterBase:
    def __init__(self, instance, dirty_doc, target: str) -> None:
        self.doc_dict = dirty_doc
        if isinstance(self.doc_dict, Document):
            self.doc_dict = dirty_doc.as_dict()

        self.instance = instance
        self.field_map = self.field_map or {}
        self.converted_doc = {}
        self._dirty_doc = dirty_doc
        self.target = target
        self.source_doctype = self._dirty_doc.get("doctype")
        self.target_doctype = get_doctype_name(
            self.source_doctype, self.target, self._dirty_doc
        )
        self.doc_can_save = True
        self.doc_can_submit = True
        self.is_dict = isinstance(dirty_doc, dict)
        self.settings = frappe.get_cached_doc("Books Sync Settings")

        if self.target == "erpn":
            child_table = self.field_map.pop("child_tables", [])
            self.field_map = {v: k for k, v in self.field_map.items()}
            self.field_map["child_tables"] = child_table


    def _convert_doc(self):
        if not self.field_map:
            return None

        self.converted_doc = {}
        self.converted_doc["doctype"] = self.target_doctype

        for field in self.doc_dict:
            fieldname = self._get_fieldname(field)

            if not fieldname:
                continue

            self.converted_doc[fieldname] = self.doc_dict.get(field)

        for child_table in (self.field_map.get("child_tables") or []):
            source_field = child_table.get("fbooks_fieldname")
            target_field = child_table.get("erpn_fieldname")

            if self.target != "erpn":
                source_field = child_table.get("erpn_fieldname")
                target_field = child_table.get("fbooks_fieldname")

            if not target_field:
                continue

            if not self.doc_dict.get(source_field):
                continue

            self.converted_doc[target_field] = []
            field_map = child_table.get("fieldmap")
            if self.target == "erpn":
                field_map = {v: k for k, v in field_map.items()}

            for row in self.doc_dict.get(source_field):
                child_doc_item = {}

                for sfield, tfield in field_map.items():
                    child_doc_item[tfield] = row.get(sfield)

                self.converted_doc[target_field].append(child_doc_item)

    def _get_fieldname(self, field):
        if field in ("doctype", "fbooksDocName",):
            return None

        if not self.field_map:
            return None

        return self.field_map.get(field)

    def _fill_missing_values_for_fbooks(self):
        pass

    def _fill_missing_values_for_erpn(self):
        pass

    def get_converted_doc(self):
        self._convert_doc()

        if self.target == "erpn":
            self._fill_missing_values_for_erpn()
        else:
            self._fill_missing_values_for_fbooks()

        return self.converted_doc

    def get_frappe_doc(self):
        if not self.target == "erpn":
            return False

        if not self.converted_doc:
            self.get_converted_doc()

        return frappe.get_doc(self.converted_doc)


def init_doc_converter(instance, doc_dict, target: str):
    doctype = doc_dict.get("doctype")
    if doctype == "Item":
        return Item(instance, doc_dict, target)

    if doctype == "Customer":
        return Customer(instance, doc_dict, target)

    if doctype == "Supplier":
        return Supplier(instance, doc_dict, target)

    if doctype in ("Sales Invoice", "SalesInvoice",):
        return SalesInvoice(instance, doc_dict, target)

    if doctype in ("Payment Entry", "Payment",):
        return PaymentEntry(instance, doc_dict, target)

    if doctype in ("Stock Entry", "StockMovement",):
        return StockEntry(instance, doc_dict, target)

    if doctype in ("Price List", "PriceList",):
        return PriceList(instance, doc_dict, target)

    if doctype in ("Item Price", "PriceListItem",):
        return ItemPrice(instance, doc_dict, target)

    if doctype in ("Serial No", "SerialNumber",):
        return SerialNumber(instance, doc_dict, target)

    if doctype == "Batch":
        return Batch(instance, doc_dict, target)

    if doctype == "UOM":
        return UOM(instance, doc_dict, target)

    if doctype in ("UOM Conversion Detail", "UOMConversionItem"):
        return UOMConversionDetail(instance, doc_dict, target)

    if doctype in ("Delivery Note", "Shipment"):
        return DeliveryNote(instance, doc_dict, target)

    if doctype == "Address":
        return Address(instance, doc_dict, target)

    return False


class Item(DocConverterBase):
    def __init__(self, instance, dirty_doc, target):
        self.field_map = {
            "image": "image",
            "item_code": "name",
            "stock_uom": "unit",
            "standard_rate": "rate",
            "description": "description",
            "gst_hsn_code": "hsnCode",
            # "barcodes": "barcode",
            "is_stock_item": "trackItem",
            "has_batch_no": "hasBatch",
            "has_serial_no": "hasSerialNumber",
            "child_tables": [
                {
                    "erpn_fieldname": "uoms",
                    "fbooks_fieldname": "uomConversions",
                    "fbooks_doctype": "UOMConversionItem",
                    "erpn_doctype": "UOM Conversion Detail",
                    "fieldmap": {"uom": "uom", "conversion_factor": "conversionFactor"},
                }
            ],
        }
        super().__init__(instance, dirty_doc, target)

    def get_item_tax_template(self, name: str, target: str):
        templates_map = {}

        sfield = "erpn_tax_template"
        tfield = "fbooks_tax_template"
        if target == "erpn":
            sfield, tfield = tfield, sfield

        for row in (self.settings.get("item_tax_template_map") or []):
            templates_map[row.get(sfield)] = row.get(tfield)

        return templates_map.get(name)

    def _fill_missing_values_for_fbooks(self):
        # self.converted_doc["rate"] = item_rate
        if not self.doc_dict.get("taxes"):
            return

        self.converted_doc["tax"] = self.get_item_tax_template(
            self.doc_dict.get("taxes")[0]["item_tax_template"], self.target
        )

    def _fill_missing_values_for_erpn(self):
        self.converted_doc["name"] = self._dirty_doc.get("name")
        self.converted_doc["item_group"] = "Products"

        if self._dirty_doc["tax"]:
            self.converted_doc["taxes"] = []
            self.converted_doc["taxes"].append(
                {
                    "item_tax_template": self.get_item_tax_template(
                        self._dirty_doc.get("tax"), self.target
                    )
                }
            )

        if len(str(self._dirty_doc.get("hsnCode"))) < 6:
            self.converted_doc["gst_hsn_code"] = "0" + str(
                self._dirty_doc.get("hsnCode")
            )

        if self.doc_dict.get("barcode"):
            self.converted_doc["barcodes"] = []
            self.converted_doc["barcodes"].append(
                {"barcode": str(self._dirty_doc.get("barcode"))}
            )


class Customer(DocConverterBase):
    def __init__(self, instance, dirty_doc, target):
        self.field_map = {
            "name": "name",
            "gstin": "gstin",
            "gst_category": "gstType",
            "customer_primary_address": "address",
        }
        super().__init__(instance, dirty_doc, target)

    def _fill_missing_values_for_erpn(self):
        self.converted_doc["customer_name"] = self._dirty_doc.get("name")
        address_name = frappe.db.get_value(
            "Books Reference",
            {
                "document_type": "Address",
                "books_name": self.converted_doc["customer_primary_address"],
                "instance": self.instance
            },
            "document_name"
        )
        self.converted_doc["customer_primary_address"]= address_name

    def _fill_missing_values_for_fbooks(self):
        self.converted_doc["role"] = "Customer"


class Supplier(DocConverterBase):
    def __init__(self, instance, dirty_doc, target):
        self.field_map = {
            "name": "name",
            "gstin": "gstin",
            "gst_category": "gstType",
            "supplier_primary_address": "address",
        }
        super().__init__(instance, dirty_doc, target)

    def _fill_missing_values_for_erpn(self):
        self.converted_doc["supplier_name"] = self._dirty_doc.get("name")

        address_name = frappe.db.get_value(
            "Books Reference",
            {
                "document_type": "Address",
                "books_name": self.converted_doc["supplier_primary_address"],
                "instance": self.instance
            },
            "document_name"
        )
        self.converted_doc["supplier_primary_address"]= address_name

    def _fill_missing_values_for_fbooks(self):
        self.converted_doc["role"] = "Supplier"


class SalesInvoice(DocConverterBase):
    def __init__(self, instance, dirty_doc, target):
        self.field_map = {
            # "name": "name",
            # "naming_series": "numberSeries",
            # "debit_to": "account",
            "customer": "party",
            "posting_date": "date",
            # "is_pos": "isPOS",
            "is_return": "isReturn",
            "return_against": "returnAgainst",
            "selling_price_list": "priceList",
            "net_total": "netTotal",
            "base_grand_total": "baseGrandTotal",
            "grand_total": "grandTotal",
            # "discount_amount": "discountAmount",
            # "discount_percentage": "discountPercent",
            "currency": "currency",
            "conversion_rate": "exchangeRate",
            "outstanding_amount": "outstandingAmount",
            "terms": "terms",
            "child_tables": [
                {
                    "erpn_fieldname": "items",
                    "fbooks_fieldname": "items",
                    "fbooks_doctype": "SalesInvoiceItem",
                    "erpn_doctype": "Sales Invoice Item",
                    "fieldmap": {
                        "item_code": "item",
                        "description": "description",
                        "qty": "quantity",
                        "stock_uom": "unit",
                        "batch_no": "batch",
                        "conversion_factor": "unitConversionFactor",
                        "discount_percentage": "itemDiscountPercent",
                        "discount_amount": "itemDiscountAmount",
                        "price_list_rate": "rate",
                        "amount": "amount",
                        # "income_account": "account",
                    },
                },
            ],
        }
        super().__init__(instance, dirty_doc, target)

    def _fill_missing_values_for_erpn(self):
        self.converted_doc["disable_rounded_total"] = 1
        self.converted_doc["set_posting_time"] = 1
        self.converted_doc["posting_date"] = getdate(
            self.converted_doc["posting_date"]
        )

        for item in self.converted_doc["items"]:
            if flt(item.get("discount_percentage")) > 0:
                discount_amount = flt(
                    (flt(item.get("price_list_rate")) * flt(item.get("discount_percentage")))
                    / 100
                )

                item["discount_amount"] = discount_amount
                item["rate"] = flt(item["price_list_rate"]) - discount_amount

    def _fill_missing_values_for_fbooks(self):
        if self._dirty_doc.get("docstatus") == 2:
            self.converted_doc["submitted"] = True
            self.converted_doc["cancelled"] = True
            return

        self.converted_doc["submitted"] = self._dirty_doc.get("docstatus")


class PaymentEntry(DocConverterBase):
    def __init__(self, instance, dirty_doc, target):
        self.field_map = {
            # "naming_series": "numberSeries",
            "posting_date": "date",
            "payment_type": "paymentType",
            "mode_of_payment": "paymentMethod",
            "party": "party",
            "total_allocated_amount": "amount",
            "paid_to": "paymentAccount",
            "child_tables": [
                {
                    "erpn_fieldname": "references",
                    "fbooks_fieldname": "for",
                    "fbooks_doctype": "PaymentFor",
                    "erpn_doctype": "Payment Entry Reference",
                    "fieldmap": {
                        "reference_name": "referenceName",
                        "reference_doctype": "referenceType",
                        "total_amount": "amount",
                    },
                },
            ],
        }
        super().__init__(instance, dirty_doc, target)

    def _fill_missing_values_for_erpn(self):
        if self._dirty_doc.get("paymentMethod") == "Transfer":
            self.converted_doc["mode_of_payment"] = "Bank Draft"

        is_party_is_customer = frappe.db.exists("Customer", self.converted_doc["party"])

        if is_party_is_customer:
            self.converted_doc["party_type"] = "Customer"
        else:
            self.converted_doc["party_type"] = "Supplier"

        self.converted_doc["received_amount"] = flt(
            self.converted_doc["total_allocated_amount"]
        )

        self.converted_doc["paid_amount"] = flt(
            self.converted_doc["total_allocated_amount"]
        )

        self.converted_doc["posting_date"] = getdate(
            self.converted_doc["posting_date"]
        )

        for row in self.converted_doc["references"]:
            reference_name_in_erpn = frappe.db.get_value(
                "Books Reference",
                {"books_name": row["reference_name"], "instance": self.instance},
                "document_name",
            )

            row["reference_name"] = reference_name_in_erpn
            row["reference_doctype"] = get_doctype_name(
                row["reference_doctype"], self.target
            )

            row["total_amount"] = float(row["total_amount"])
            row["allocated_amount"] = float(row["total_amount"])


class StockEntry(DocConverterBase):
    def __init__(self, instance, dirty_doc, target):
        self.field_map = {
            # "naming_series": "numberSeries",
            "name": "name",
            "stock_entry_type": "movementType",
            "posting_date": "date",
            "total_amount": "amount",
            "child_tables": [
                {
                    "erpn_fieldname": "items",
                    "fbooks_fieldname": "items",
                    "fbooks_doctype": "StockMovementItem",
                    "erpn_doctype": "Stock Entry Detail",
                    "fieldmap": {
                        "s_warehouse": "fromLocation",
                        "t_warehouse": "toLocation",
                        "item_code": "item",
                        "qty": "quantity",
                        "transfer_qty": "transferQuantity",
                        "uom": "transferUnit",
                        "stock_uom": "unit",
                        "conversion_factor": "unitConversionFactor",
                        "basic_rate": "rate",
                        "amount": "amount",
                        "serial_no": "serialNumber",
                    },
                }
            ],
        }
        super().__init__(instance, dirty_doc, target)

    def _fill_missing_values_for_erpn(self):
        if "Material" in self.converted_doc["stock_entry_type"]:
            entry_type = self.converted_doc["stock_entry_type"].split("Material")[1]
            self.converted_doc["stock_entry_type"] = "Material {}".format(entry_type)
            self.converted_doc["purpose"] = "Material {}".format(entry_type)

    def _fill_missing_values_for_fbooks(self):
        if self._dirty_doc.get("docstatus") == 2:
            self.converted_doc["submitted"] = True
            self.converted_doc["cancelled"] = True
        else:
            self.converted_doc["submitted"] = bool(self._dirty_doc.get("docstatus"))

        self.converted_doc["movementType"] = "".join(
            self.converted_doc["movementType"].split()
        )

        for item in self.converted_doc["items"]:
            self.converted_doc["serial_no"] = not item.get(
                "use_serial_batch_fields"
            ) and item.get("serial_and_batch_bundle")

            item["serial_no"] = item.get("item_code")
            if not item.get("use_serial_batch_fields") and item.get(
                "serial_and_batch_bundle"
            ):
                sn_batch_bundle = frappe.get_doc(
                    "Serial and Batch Bundle", item.get("serial_and_batch_bundle")
                )

                item["serial_no"] = sn_batch_bundle.get("entries")
                if sn_batch_bundle.get("entries"):
                    for sn in sn_batch_bundle.get("entries"):
                        serial_nos += sn.get("serial_no") + "\n"

                item["serial_no"] = serial_nos
                # add batch as well


class PriceList(DocConverterBase):
    def __init__(self, instance, dirty_doc, target):
        self.field_map = {
            "name": "name",
            "enabled": "isEnabled",
            "price_list_name": "name",
            "buying": "isPurchase",
            "selling": "isSelling",
            "child_tables": [
                {
                    "erpn_fieldname": "",
                    "fbooks_fieldname": "priceListItem",
                    "fbooks_doctype": "PriceListItem",
                    "erpn_doctype": "Item Price",
                    "fieldmap": {
                        "name": "name",
                        "item_code": "item",
                        "uom": "unit",
                        "price_list": "parent",
                        "price_list_rate": "rate",
                    },
                }
            ],
        }
        super().__init__(instance, dirty_doc, target)


class ItemPrice(DocConverterBase):
    def __init__(self, instance, dirty_doc, target):
        self.field_map = {
            "name": "name",
            "item_code": "item",
            "uom": "unit",
            "price_list": "parent",
            "price_list_rate": "rate",
        }
        super().__init__(instance, dirty_doc, target)

    def _fill_missing_values_for_fbooks(self):
        self.converted_doc["parentSchemaName"] = get_doctype_name(
            "Price List", "fbooks"
        )
        self.converted_doc["parentFieldname"] = "priceListItem"


class SerialNumber(DocConverterBase):
    def __init__(self, instance, dirty_doc, target):
        self.field_map = {
            "serial_no": "name",
            "item_code": "item",
            "description": "description",
        }
        super().__init__(instance, dirty_doc, target)


class Batch(DocConverterBase):
    def __init__(self, instance, dirty_doc, target):
        self.field_map = {
            "batch_id": "name",
            "expiry_date": "expiryDate",
            "manufacturing_date": "manufactureDate",
        }
        super().__init__(instance, dirty_doc, target)


class UOM(DocConverterBase):
    def __init__(self, instance, dirty_doc, target):
        self.field_map = {
            "name": "name",
            "must_be_whole_number": "isWhole",
            "uom_name": "name",
        }
        super().__init__(instance, dirty_doc, target)


class UOMConversionDetail(DocConverterBase):
    def __init__(self, instance, dirty_doc, target):
        self.field_map = {"uom": "uom", "conversion_factor": "conversionFactor"}
        super().__init__(instance, dirty_doc, target)


class DeliveryNote(DocConverterBase):
    def __init__(self, instance, dirty_doc, target):
        self.field_map = {
            # "naming_series": "numberSeries",
            "customer": "party",
            "posting_date": "date",
            "grand_total": "grandTotal",
            "child_tables": [
                {
                    "erpn_fieldname": "items",
                    "fbooks_fieldname": "items",
                    "fbooks_doctype": "ShipmentItem",
                    "erpn_doctype": "Delivery Note Item",
                    "fieldmap": {
                        "item_code": "item",
                        "qty": "quantity",
                        "uom": "unit",
                        "rate": "rate",
                        "warehouse": "location",
                    },
                }
            ],
        }
        super().__init__(instance, dirty_doc, target)

    def _fill_missing_values_for_erpn(self):
        if self.doc_dict.get("backReference"):
            for row in self.converted_doc["items"]:
                try:
                    reference_name_in_erpn = frappe.db.get_value(
                        "Books Reference",
                        {"books_name": self.doc_dict.get("backReference"), "instance": self.instance},
                        "document_name",
                    )

                    if reference_name_in_erpn:
                        row["against_sales_invoice"] = reference_name_in_erpn

                        inv_item_name, inv_item_rate = frappe.db.get_value(
                            "Sales Invoice Item",
                            {
                                "parent": reference_name_in_erpn,
                                "item_code": row["item_code"],
                            },
                            ["name", "amount"],
                        )

                    if inv_item_name:
                        row["si_detail"] = inv_item_name

                    if inv_item_rate:
                        row["billed_amt"] = inv_item_rate
                except:
                    pass

    def before_save(self):
        ref_doc_name = self._dirty_doc.get("backReference")
        if not ref_doc_name:
            self.doc_can_save = True

        ref_doc_name_in_erpnext = frappe.db.get_value(
            "Books Reference", {"books_name": ref_doc_name, "instance": self.instance}, "name"
        )

        if not ref_doc_name_in_erpnext:
            self.doc_can_save = False

        doc_status = frappe.db.get_value(
            "Sales Invoice", ref_doc_name_in_erpnext, "docstatus"
        )

        if doc_status == 0:
            return False

        self.doc_can_save = True


class Address(DocConverterBase):
    def __init__(self, instance, dirty_doc, target):
        self.field_map = {
            "name": "name",
            "address_line1": "addressLine1",
            "address_line2": "addressLine2",
            "city": "city",
            "state": "state",
            "country": "country",
            "pincode": "postalCode",
        }
        super().__init__(instance, dirty_doc, target)

    def _fill_missing_values_for_erpn(self):
        self.converted_doc["address_title"] = self.converted_doc.get("name")
