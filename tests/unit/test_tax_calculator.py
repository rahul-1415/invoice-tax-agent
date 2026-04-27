from src.models import LineItem, Invoice
from src.tax_calculator import TaxCalculator


def test_subtotal():
    calc = TaxCalculator()
    invoice = Invoice(
        invoice_id="INV-001", vendor="ACME", date="2024-01-15",
        line_items=[
            LineItem(description="Item A", total_amount=100.0),
            LineItem(description="Item B", total_amount=200.0),
        ]
    )
    assert calc.subtotal(invoice) == 300.0


def test_calculate_tax():
    calc = TaxCalculator()
    assert calc.calculate_tax(100.0, 0.08) == 8.0
    assert calc.calculate_tax(0.0, 0.08) == 0.0
    assert calc.calculate_tax(100.0, 0.0) == 0.0


def test_calculate_line_items():
    calc = TaxCalculator()
    items = [
        LineItem(description="Laptop", total_amount=1000.0),
        LineItem(description="Apples", total_amount=10.0),
    ]
    classifications = [
        {"category": "Electronics", "tax_rate": 0.08},
        {"category": "Fresh Produce", "tax_rate": 0.0},
    ]
    result = calc.calculate_line_items(items, classifications)
    assert len(result) == 2
    assert result[0].tax_amount == 80.0
    assert result[1].tax_amount == 0.0


def test_calculate_full():
    calc = TaxCalculator()
    invoice = Invoice(
        invoice_id="INV-001", vendor="ACME", date="2024-01-15",
        line_items=[LineItem(description="Laptop", total_amount=1000.0)]
    )
    classifications = [{"category": "Electronics", "tax_rate": 0.08}]
    result = calc.calculate(invoice, classifications)
    assert result.subtotal == 1000.0
    assert result.total_tax == 80.0
    assert result.grand_total == 1080.0
    assert result.invoice_id == "INV-001"
