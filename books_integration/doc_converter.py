import frappe
from frappe.utils import flt
from fb_int.utils import get_doctype_name, convert_date_for_frappe


class DocConverterBase:
    def __init__(self, dirty_doc, target: str) -> None:
        if isinstance(dirty_doc, dict):
            self.doc_dict = dirty_doc
        else:
            self.doc_dict = dirty_doc.as_dict()

        self.field_map = dict()
        self.converted_doc = dict()
        self._dirty_doc = dirty_doc
        self.target = target
        self.source_doctype = self._dirty_doc.get("doctype")
        self.target_doctype = get_doctype_name(
            self.source_doctype, self.target, self._dirty_doc
        )
        self.frappe_doc = None
        self.doc_can_save = True
        self.doc_can_submit = True
        self.is_dict = isinstance(dirty_doc, dict)

    def _convert_doc(self):

        if not self.field_map:
            return None

        self.converted_doc["doctype"] = self.target_doctype

        for field in self.doc_dict:
            fieldname = self._get_fieldname(field)

            if not fieldname:
                continue

            self.converted_doc[fieldname] = self.doc_dict.get(field)

        if self.field_map.get("child_tables"):
            for child_table in self.field_map.get("child_tables"):

                if self.target == "erpn":
                    source_table_fieldname = child_table.get("fbooks_fieldname")
                    target_table_fieldname = child_table.get("erpn_fieldname")
                    if not child_table.get("erpn_fieldname"):
                        continue
                else:
                    source_table_fieldname = child_table.get("erpn_fieldname")
                    target_table_fieldname = child_table.get("fbooks_fieldname")
                    if not child_table.get("fbooks_fieldname"):
                        continue

                if not self.doc_dict.get(source_table_fieldname):
                    continue

                self.converted_doc[target_table_fieldname] = []

                for row in self.doc_dict.get(source_table_fieldname):
                    child_doc_item = {}

                    field_map = child_table.get("fieldmap")

                    for field in field_map:
                        if self.target == "erpn":
                            source_fieldname_idx = list(field_map.keys()).index(field)
                            source_fieldname = list(field_map.values())[
                                source_fieldname_idx
                            ]
                            target_fieldname = field
                            pass
                        else:
                            source_fieldname = field
                            target_fieldname = field_map.get(field)
                            fieldname = field

                        child_doc_item[target_fieldname] = row.get(source_fieldname)

                    self.converted_doc[target_table_fieldname].append(child_doc_item)

    def _get_fieldname(self, field):
        if field == "doctype" or field == "fbooksDocName":
            return False

        if not self.field_map:
            return False

        return self._get_fieldname_from_map(field)

    def _get_fieldname_from_map(self, field):
        try:
            if self.target == "erpn":
                field_name_idx = list(self.field_map.values()).index(field)
                key_name = list(self.field_map.keys())[field_name_idx]

            else:
                if not self.field_map[field]:
                    return False

                key_name = self.field_map[field]

            return key_name
        except:
            return False

    def _fill_missing_values_for_fbooks(self):
        pass

    def _fill_missing_values_for_erpn(self):
        pass

    def get_doc_as_list(self):
        return self.doc_dict or False

    def get_converted_doc(self):
        self._convert_doc()

        if self.target == "erpn":
            self._fill_missing_values_for_erpn()
        else:
            self._fill_missing_values_for_fbooks()

        return self.converted_doc or False

    def get_frappe_doc(self):
        if not self.target == "erpn":
            return False

        self.frappe_doc = frappe.get_doc(self.converted_doc)
        return self.frappe_doc

    def run_doc_method(self, method: str):
        try:
            func = getattr(self, method, False)
            func()
        except:
            return

    def after_save(self):
        pass

    def after_cancel(self):
        pass


def DocConverter(dirty_doc, target: str):
    if isinstance(dirty_doc, dict):
        doc_dict = dirty_doc
    else:
        doc_dict = dirty_doc
        doc_dict.doctype = dirty_doc.get("doctype")

    match dirty_doc.get("doctype"):
        case "Item":
            return Item(doc_dict, target)

        case "Customer":
            return Customer(doc_dict, target)

        case "Supplier":
            return Supplier(doc_dict, target)

        case "Sales Invoice" | "SalesInvoice":
            return SalesInvoice(doc_dict, target)

        case "Payment Entry" | "Payment":
            return PaymentEntry(doc_dict, target)

        case "Stock Entry" | "StockMovement":
            return StockEntry(doc_dict, target)

        case "Price List" | "PriceList":
            return PriceList(doc_dict, target)

        case "Item Price" | "PriceListItem":
            return ItemPrice(doc_dict, target)

        case "Serial No" | "SerialNumber":
            return SerialNumber(doc_dict, target)

        case "Batch":
            return Batch(doc_dict, target)

        case "UOM":
            return UOM(doc_dict, target)

        case "UOM Conversion Detail" | "UOMConversionItem":
            return UOMConversionDetail(doc_dict, target)

        case "Delivery Note" | "Shipment":
            return DeliveryNote(doc_dict, target)

        case "Address":
            return Address(doc_dict, target)

        case _:
            return False


class Item(DocConverterBase):
    def __init__(self, dirty_doc, target):
        super().__init__(dirty_doc, target)

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

    def get_item_tax_template(self, name: str, target: str):
        sync_settings = frappe.get_doc("FBooks Sync Settings", {"enable_sync": 1})
        item_tax_templates = sync_settings.get("item_tax_template_map")
        templates_map = dict()

        for row in item_tax_templates:
            templates_map[row.get("erpn_tax_template")] = row.get("fbooks_tax_template")

        try:
            if target == "erpn":
                idx = list(templates_map.values()).index(name)
                return list(templates_map.keys())[idx]
            else:
                idx = list(templates_map.keys()).index(name)

                return list(templates_map.values())[idx]
        except:
            return None

    def _fill_missing_values_for_fbooks(self):
        item_price_docs = frappe.db.get_list(
            "Item Price",
            filters={
                "item_code": self._dirty_doc.get("name"),
                "price_list": "Standard Selling",
            },
            fields=["rate"],
        )

        if len(item_price_docs):
            self.converted_doc["rate"] = item_price_docs[0][0]

        if len(self.doc_dict.get("taxes")):
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

    def after_save(self):
        item_price_docs = frappe.db.get_list(
            "Item Price",
            filters={
                "item_code": self._dirty_doc.get("name"),
                "price_list": "Standard Selling",
            },
            fields=["name"],
        )

        if not item_price_docs:
            return

        item_price_docname = item_price_docs[0].get("name")

        item_price_doc = frappe.get_doc("Item Price", item_price_docname)
        item_price_doc.price_list_rate = self._dirty_doc.get("rate")
        item_price_doc.save(ignore_permissions=True)


class Customer(DocConverterBase):
    def __init__(self, dirty_doc, target):
        super().__init__(dirty_doc, target)

        self.field_map = {
            "name": "name",
            "gstin": "gstin",
            "gst_category": "gstType",
            "address": "customer_primary_address",
        }

    def _fill_missing_values_for_erpn(self):
        self.converted_doc["customer_name"] = self._dirty_doc.get("name")

    def _fill_missing_values_for_fbooks(self):
        self.converted_doc["role"] = "Customer"


class Supplier(DocConverterBase):
    def __init__(self, dirty_doc, target):
        super().__init__(dirty_doc, target)

        self.field_map = {"name": "name", "gstin": "gstin", "gst_category": "gstType"}

    def _fill_missing_values_for_erpn(self):
        self.converted_doc["supplier_name"] = self._dirty_doc.get("name")

    def _fill_missing_values_for_fbooks(self):
        self.converted_doc["role"] = "Supplier"


class SalesInvoice(DocConverterBase):
    def __init__(self, dirty_doc, target):
        super().__init__(dirty_doc, target)

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
                        "rate": "rate",
                        "amount": "amount",
                        "base_rate": "rate",
                        # "income_account": "account",
                    },
                },
            ],
        }

    def _fill_missing_values_for_erpn(self):
        self.converted_doc["disable_rounded_total"] = 1
        self.converted_doc["set_posting_time"] = 1
        self.converted_doc["posting_date"] = convert_date_for_frappe(
            self.converted_doc["posting_date"]
        )

        if not self.converted_doc["selling_price_list"]:
            self.converted_doc["selling_price_list"] = "Standard Selling"

        for item in self.converted_doc["items"]:
            if flt(item.get("discount_percentage")) > 0:
                discount_amount = flt(
                    (flt(item.get("amount")) * flt(item.get("discount_percentage")))
                    / 100
                )

                item["discount_amount"] = discount_amount
                item["rate"] = flt(item["amount"]) - discount_amount


    def _fill_missing_values_for_fbooks(self):
        if self._dirty_doc.get("docstatus") == 2:
            self.converted_doc["submitted"] = True
            self.converted_doc["cancelled"] = True
        else:
            self.converted_doc["submitted"] = self._dirty_doc.get("docstatus")

    def before_save(self):
        pass


class PaymentEntry(DocConverterBase):
    def __init__(self, dirty_doc, target):
        super().__init__(dirty_doc, target)

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

    def _fill_missing_values_for_erpn(self):
        if self._dirty_doc.get("paymentMethod") == "Transfer":
            self.converted_doc["mode_of_payment"] = "Bank Draft"

        is_party_is_customer = frappe.db.exists("Customer", self.converted_doc["party"])

        if is_party_is_customer:
            self.converted_doc["party_type"] = "Customer"
        else:
            self.converted_doc["party_type"] = "Supplier"

        self.converted_doc["received_amount"] = float(
            self.converted_doc["total_allocated_amount"]
        )

        self.converted_doc["paid_amount"] = float(
            self.converted_doc["total_allocated_amount"]
        )

        self.converted_doc["posting_date"] = convert_date_for_frappe(
            self.converted_doc["posting_date"]
        )

        for row in self.converted_doc["references"]:
            reference_name_in_erpn = frappe.db.get_value(
                "Books ERPN Doc Name",
                {"name_in_fbooks": row["reference_name"]},
                "name_in_erpnext",
            )

            row["reference_name"] = reference_name_in_erpn
            row["reference_doctype"] = get_doctype_name(
                row["reference_doctype"], self.target
            )

            row["total_amount"] = float(row["total_amount"])
            row["allocated_amount"] = float(row["total_amount"])


class StockEntry(DocConverterBase):
    def __init__(self, dirty_doc, target):
        super().__init__(dirty_doc, target)

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

    def fill_missing_values_for_erpn(self):
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


class PriceList(DocConverterBase):
    def __init__(self, dirty_doc, target):
        super().__init__(dirty_doc, target)

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


class ItemPrice(DocConverterBase):
    def __init__(self, dirty_doc, target):
        super().__init__(dirty_doc, target)

        self.field_map = {
            "name": "name",
            "item_code": "item",
            "uom": "unit",
            "price_list": "parent",
            "price_list_rate": "rate",
        }

    def _fill_missing_values_for_fbooks(self):
        self.converted_doc["parentSchemaName"] = get_doctype_name(
            "Price List", "fbooks"
        )
        self.converted_doc["parentFieldname"] = "priceListItem"


class SerialNumber(DocConverterBase):
    def __init__(self, dirty_doc, target):
        super().__init__(dirty_doc, target)
        self.field_map = {
            "serial_no": "name",
            "item_code": "item",
            "description": "description",
        }


class Batch(DocConverterBase):
    def __init__(self, dirty_doc, target):
        super().__init__(dirty_doc, target)
        self.field_map = {
            "batch_id": "name",
            "expiry_date": "expiryDate",
            "manufacturing_date": "manufactureDate",
        }


class UOM(DocConverterBase):
    def __init__(self, dirty_doc, target):
        super().__init__(dirty_doc, target)
        self.field_map = {
            "name": "name",
            "must_be_whole_number": "isWhole",
            "uom_name": "name",
        }


class UOMConversionDetail(DocConverterBase):
    def __init__(self, dirty_doc, target):
        super().__init__(dirty_doc, target)
        self.field_map = {"uom": "uom", "conversion_factor": "conversionFactor"}


class DeliveryNote(DocConverterBase):
    def __init__(self, dirty_doc, target):
        super().__init__(dirty_doc, target)
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

    def _fill_missing_values_for_erpn(self):
        if self.doc_dict.get("backReference"):
            for row in self.converted_doc["items"]:
                try:
                    reference_name_in_erpn = frappe.db.get_value(
                        "Books ERPN Doc Name",
                        {"name_in_fbooks": self.doc_dict.get("backReference")},
                        "name_in_erpnext",
                    )

                    if reference_name_in_erpn:
                        row["against_sales_invoice"] = reference_name_in_erpn

                        inv_item_name, inv_item_rate = frappe.db.get_value(
                            "Sales Invoice Item",
                            {
                                "parent": reference_name_in_erpn,
                                "item_code": "Banana",
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
            "Books ERPN Doc Name", {"name_in_fbooks": ref_doc_name}, "name"
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
    def __init__(self, dirty_doc, target):
        super().__init__(dirty_doc, target)
        self.field_map = {
            "name": "name",
            "address_line1": "addressLine1",
            "address_line2": "addressLine2",
            "city": "city",
            "state": "state",
            "country": "country",
            "pincode": "postalCode",
        }
