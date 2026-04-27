import os
import pytest
from openai import OpenAI
from src.invoice_extractor import InvoiceExtractor
from src.tax_classifier import TaxClassifier
from src.tax_calculator import TaxCalculator
from src.agent import Agent


@pytest.fixture
def agent():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENAI_API_KEY not set")
    client = OpenAI(api_key=api_key)
    classifier = TaxClassifier("tax_rate_by_category.csv")
    calculator = TaxCalculator()
    return Agent(client, classifier, calculator)


@pytest.fixture
def extractor():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENAI_API_KEY not set")
    return InvoiceExtractor(OpenAI(api_key=api_key))


def test_full_workflow(agent, extractor):
    """Extract a PDF invoice, classify line items, calculate tax, print result."""
    pdf_path = "test-docs/R-1093-12322.pdf"
    if not os.path.exists(pdf_path):
        pytest.skip(f"{pdf_path} not found")

    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    invoice = extractor.extract(pdf_bytes, "pdf")
    result = agent.process_invoice(invoice, extraction_method="pdf")

    assert result["invoice_id"]
    assert result["vendor"]
    assert result["subtotal"] > 0
    assert result["grand_total"] >= result["subtotal"]
    assert len(result["line_items"]) > 0

    print(f"\n{'='*50}")
    print(f"Vendor:      {result['vendor']}")
    print(f"Date:        {result['date']}")
    print(f"Tax Exempt:  {result['tax_exempt']}")
    print(f"Subtotal:    ${result['subtotal']:.2f}")
    print(f"Total Tax:   ${result['total_tax']:.2f}")
    print(f"Grand Total: ${result['grand_total']:.2f}")
    print(f"\nLine Items:")
    for item in result["line_items"]:
        print(f"  - {item['description']}: ${item['total_amount']:.2f} | {item['category']} @ {item['tax_rate']*100:.1f}%")
    print(f"{'='*50}")
