from dataclasses import dataclass, field
from typing import Optional

# This module defines the data models for the invoice tax calculation system (Read sample docs to understand the structure).

@dataclass
class LineItem:
    description: str
    total_amount: float
    quantity: Optional[float] = None # Quantity is optional because some line items did not contain a quantity in the sample docs provided.
    unit_price: Optional[float] = None # Unit price is optional because some line items did not contain a unit price in the sample docs provided.


@dataclass
class Address:
    street: str
    city: str
    state: str
    zip_code: str
    country: Optional[str] = None

# Noted this on my re-work of the application. (All the sample invoices provided had a contact person listed with a name and phone number)
@dataclass
class Contact:
    name: str
    phone: Optional[str] = None

@dataclass
class Invoice:
    invoice_id: str
    vendor: str
    date: str
    line_items: list[LineItem] = field(default_factory=list) # field(default_factory=list) is used to provide a default empty list for line_items, prevents invoice instances from sharing the same list .
    tax_exempt: bool = False # Tax exempt status is optional and defaults to False. In the sample documents, some invoices are marked as tax exempt.
    tax_exempt_reason: Optional[str] = None # Tax exempt reason is optional and defaults to None.
    vendor_address: Optional[Address] = None
    bill_to_name: Optional[str] = None
    bill_to_address: Optional[Address] = None
    customer_id: Optional[str] = None
    due_date: Optional[str] = None
    contact_person: Optional[Contact] = None


@dataclass
class LineItemTax:
    description: str
    category: str #get from tax-classifier
    tax_rate: float #get from tax-classifier
    tax_amount: float #get from tax-calculator
    total_amount: float #get from tax-calculator


@dataclass
class TaxResult:
    invoice_id: str
    vendor: str
    date: str
    subtotal: float
    total_tax: float
    grand_total: float
    tax_exempt: bool
    line_item_taxes: list[LineItemTax] = field(default_factory=list) # field(default_factory=list) is used to provide a default empty list for line_item_taxes, prevents TaxResult instances from sharing the same list .
    vendor_address: Optional[Address] = None
    bill_to_name: Optional[str] = None
    bill_to_address: Optional[Address] = None
    customer_id: Optional[str] = None
    due_date: Optional[str] = None
    contact_person: Optional[Contact] = None
    extraction_method: Optional[str] = None  # pdf parsing or openai vision model
    processed_at: Optional[str] = None # for audit and debugging purposes, we can track when the invoice was processed.

    # The to_dict method converts the TaxResult dataclass instance into a dictionary format that can be easily serialized to JSON or stored in a database. It also handles the conversion of nested Address and Contact dataclasses into dictionaries.
    def to_dict(self) -> dict:
        def address_to_dict(addr: Optional[Address]) -> Optional[dict]:
            if not addr:
                return None
            return {
                "street": addr.street,
                "city": addr.city,
                "state": addr.state,
                "zip_code": addr.zip_code,
                "country": addr.country,
            }

        def contact_to_dict(contact: Optional[Contact]) -> Optional[dict]:
            if not contact:
                return None
            return {
                "name": contact.name,
                "phone": contact.phone,
            }

        return {
            "invoice_id": self.invoice_id,
            "vendor": self.vendor,
            "date": self.date,
            "subtotal": self.subtotal,
            "total_tax": self.total_tax,
            "grand_total": self.grand_total,
            "tax_exempt": self.tax_exempt,
            "vendor_address": address_to_dict(self.vendor_address),
            "bill_to_name": self.bill_to_name,
            "bill_to_address": address_to_dict(self.bill_to_address),
            "customer_id": self.customer_id,
            "due_date": self.due_date,
            "contact_person": contact_to_dict(self.contact_person),
            "extraction_method": self.extraction_method,
            "processed_at": self.processed_at,
            "line_items": [
                {
                    "description": t.description,
                    "category": t.category,
                    "tax_rate": t.tax_rate,
                    "tax_amount": t.tax_amount,
                    "total_amount": t.total_amount,
                }
                for t in self.line_item_taxes
            ],
        }