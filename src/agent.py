import json
from unicodedata import category
from openai import OpenAI
from src.models import Invoice
from src.tax_classifier import TaxClassifier
from src.tax_calculator import TaxCalculator


class Agent:

    # Inject classifier, calculator and openai client
    def __init__(self, openai_client: OpenAI, tax_classifier: TaxClassifier, tax_calculator: TaxCalculator):
        self.client = openai_client
        self.classifier = tax_classifier
        self.calculator = tax_calculator
    
    # Process invoices: check tax exempt status -> classify line items -> calculate taxes -> return results.
    def process_invoice(self, invoice: Invoice, extraction_method: str = None) -> dict:
        if invoice.tax_exempt:
            return self._handle_tax_exempt(invoice, extraction_method)
        
        classifications = self._classify_line_items(invoice)
        tax_result = self.calculator.calculate(invoice, classifications)
        
        if extraction_method:
            tax_result.extraction_method = extraction_method
        
        return tax_result.to_dict()
    
    # Uses the tax classifier to classify each line item in the invoice into a tax category using openai and retrieve the corresponding tax rate.
    def _classify_line_items(self, invoice: Invoice) -> list:
        classifications = []
        category_text = self.classifier.get_categories_text()
        
        for line_item in invoice.line_items:
            response = self.client.messages.create(
                model="gpt-4o",
                messages=[{
                    "role": "user",
                    "content": f"""Classify this line item to the closest tax category.
                    Line item: {line_item.description}
                    Available categories: {category_text}
                    Return JSON only:
                    {{"category": "<category name>"}}"""
                }],
                response_format={"type": "json_object"},
                temperature=0,
            )
            
            data = json.loads(response.content[0].text)            
            category = data.get("category")

            if not category or not self.classifier.is_valid_category(category):
                raise ValueError(f"Could not identify tax category for '{line_item.description}'. Manual review needed.")

            tax_rate = self.classifier.get_rate(category)
            
            classifications.append({
                "category": category,
                "tax_rate": tax_rate
            })
        
        return classifications
    
    # If the invoice is marked as tax exempt, we skip classification and calculation, and return a TaxResult with tax_exempt true.
    def _handle_tax_exempt(self, invoice: Invoice, extraction_method: str = None) -> dict:
        from src.models import TaxResult, LineItemTax
        
        line_item_taxes = [
            LineItemTax(
                description=item.description,
                category="Tax Exempt",
                tax_rate=0.0,
                tax_amount=0.0,
                total_amount=item.total_amount
            )
            for item in invoice.line_items
        ]
        
        result = TaxResult(
            invoice_id=invoice.invoice_id,
            vendor=invoice.vendor,
            date=invoice.date,
            subtotal=invoice.subtotal,
            total_tax=0.0,
            grand_total=invoice.subtotal,
            tax_exempt=True,
            line_item_taxes=line_item_taxes,
            vendor_address=invoice.vendor_address,
            bill_to_name=invoice.bill_to_name,
            bill_to_address=invoice.bill_to_address,
            customer_id=invoice.customer_id,
            due_date=invoice.due_date,
            contact_person=invoice.contact_person,
            tax_exempt_reason=invoice.tax_exempt_reason,
            extraction_method=extraction_method,
        )
        
        return result.to_dict()