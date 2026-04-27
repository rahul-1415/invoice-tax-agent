import os
import pytest
from openai import OpenAI
from src.invoice_extractor import InvoiceExtractor


@pytest.fixture
def extractor():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENAI_API_KEY not set")
    return InvoiceExtractor(OpenAI(api_key=api_key))


def test_unsupported_file_type(extractor):
    with pytest.raises(ValueError):
        extractor.extract(b"data", "docx")


def test_extract_pdf(extractor):
    pdf_path = "test-docs/RetailCo_Invoice.pdf"
    if not os.path.exists(pdf_path):
        pytest.skip(f"{pdf_path} not found")

    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    invoice = extractor.extract(pdf_bytes, "pdf")

    assert invoice.invoice_id
    assert invoice.vendor
    assert invoice.date
    assert len(invoice.line_items) > 0

    print(f"\nExtracted: {invoice.vendor} | {invoice.date} | {len(invoice.line_items)} line items")
    for item in invoice.line_items:
        print(f"  - {item.description}: ${item.total_amount}")
