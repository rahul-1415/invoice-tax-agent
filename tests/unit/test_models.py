from src.models import LineItem, Invoice, LineItemTax, TaxResult


def test_line_item():
    item = LineItem(description="Laptop", total_amount=999.99, quantity=1, unit_price=999.99)
    assert item.description == "Laptop"
    assert item.total_amount == 999.99
    assert item.quantity == 1


def test_invoice():
    items = [
        LineItem(description="Laptop", total_amount=999.99),
        LineItem(description="Mouse", total_amount=29.99),
    ]
    invoice = Invoice(invoice_id="INV-001", vendor="ACME", date="2024-01-15", line_items=items)
    assert invoice.invoice_id == "INV-001"
    assert len(invoice.line_items) == 2
    assert invoice.tax_exempt is False


def test_tax_result_to_dict():
    tax = LineItemTax(description="Laptop", category="Electronics", tax_rate=0.08, tax_amount=80.0, total_amount=1000.0)
    result = TaxResult(
        invoice_id="INV-001",
        vendor="ACME",
        date="2024-01-15",
        subtotal=1000.0,
        total_tax=80.0,
        grand_total=1080.0,
        tax_exempt=False,
        line_item_taxes=[tax],
    )
    d = result.to_dict()
    assert d["invoice_id"] == "INV-001"
    assert d["subtotal"] == 1000.0
    assert d["total_tax"] == 80.0
    assert d["grand_total"] == 1080.0
    assert len(d["line_items"]) == 1
    assert d["line_items"][0]["category"] == "Electronics"
