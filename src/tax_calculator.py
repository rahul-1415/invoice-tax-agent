from src.models import LineItem, Invoice, LineItemTax, TaxResult


class TaxCalculator:
    # Method to calculate tax
    def calculate_tax(self, amount: float, tax_rate: float) -> float:
        return round(amount * tax_rate, 2)
    
    # Calculate the tax for all line items, and returns a list containing the tax details for each line item.
    def calculate_line_items(self, line_items: list, classifications: list) -> list:
        line_item_taxes = []
        for line_item, classification in zip(line_items, classifications):
            tax_amount = self.calculate_tax(line_item.total_amount, classification["tax_rate"])
            line_item_taxes.append(LineItemTax(
                description=line_item.description,
                category=classification["category"],
                tax_rate=classification["tax_rate"],
                tax_amount=tax_amount,
                total_amount=line_item.total_amount
            ))
        return line_item_taxes
    
    # Calucalte the subtotal, total tax, and grand total for the invoice based on the line item taxes calculated.
    def calculate_totals(self, invoice: Invoice, line_item_taxes: list) -> dict:
        subtotal = invoice.subtotal
        total_tax = sum(item.tax_amount for item in line_item_taxes)
        grand_total = round(subtotal + total_tax, 2)
        return {
            "subtotal": subtotal,
            "total_tax": total_tax,
            "grand_total": grand_total
        }
    
    # Return TaxResult containing all the tax details for the invoice.
    def calculate(self, invoice: Invoice, classifications: list) -> TaxResult:
        line_item_taxes = self.calculate_line_items(invoice.line_items, classifications)
        totals = self.calculate_totals(invoice, line_item_taxes)
        
        return TaxResult(
            invoice_id=invoice.invoice_id,
            vendor=invoice.vendor,
            date=invoice.date,
            subtotal=totals["subtotal"],
            total_tax=totals["total_tax"],
            grand_total=totals["grand_total"],
            tax_exempt=invoice.tax_exempt,
            line_item_taxes=line_item_taxes,
            vendor_address=invoice.vendor_address,
            bill_to_name=invoice.bill_to_name,
            bill_to_address=invoice.bill_to_address,
            customer_id=invoice.customer_id,
            due_date=invoice.due_date,
            contact_person=invoice.contact_person
        )
