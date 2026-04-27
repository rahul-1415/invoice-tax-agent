import pymupdf
import base64
import json
import pytesseract
import io
from PIL import Image
import uuid
from src.models import Invoice, LineItem, Address, Contact

# Extraction Prompt - retained from old code.
EXTRACTION_PROMPT = """You are extracting structured data from an invoice.

Return ONLY valid JSON with this exact structure:
{
  "invoice_id": "<invoice number or generated uuid if not found>",
  "vendor": "<vendor/company name>",
  "vendor_address": {
    "street": "<street or null>",
    "city": "<city or null>",
    "state": "<state or null>",
    "zip_code": "<zip or null>"
  },
  "bill_to_name": "<bill-to name or null>",
  "bill_to_address": {
    "street": "<street or null>",
    "city": "<city or null>",
    "state": "<state or null>",
    "zip_code": "<zip or null>"
  },
  "customer_id": "<customer ID or null>",
  "date": "<invoice date as string>",
  "due_date": "<due date as string or null>",
  "contact_person": {
    "name": "<contact person name or null>",
    "phone": "<phone number or null>"
  },
  "tax_exempt": <true or false>,
  "tax_exempt_reason": "<'pre_taxed' | 'used_products' | null>",
  "line_items": [
    {
      "description": "<product description>",
      "quantity": <number or null>,
      "unit_price": <number or null>,
      "total_amount": <number>
    }
  ]
}

Rules:
- tax_exempt: scan entire invoice for "tax included", "pre-taxed", "used goods"
- total_amount: always required. Strip $ and commas.
- Return null for missing fields.
- Do not include any text outside the JSON object.

"""


class InvoiceExtractor:
    MIN_TEXT_LENGTH = 50
    
    def __init__(self, openai_client):
        self.client = openai_client
    
    # Extract based on file type, supports PDF and images.
    def extract(self, file_bytes: bytes, file_type: str) -> Invoice:
        if file_type == "pdf":
            return self._extract_from_pdf(file_bytes)
        elif file_type in ["image", "jpg", "png"]:
            return self._extract_from_image(file_bytes)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
    
    # Extract text from PDF
    # ref: https://github.com/pymupdf/pymupdf
    def _extract_from_pdf(self, pdf_bytes: bytes) -> Invoice:
        doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        
        if len(text.strip()) >= self.MIN_TEXT_LENGTH:
            return self._parse_with_gpt(text)
        else:
            return self._extract_with_vision(pdf_bytes)
    
    # Extract text from image. Try OCR first, if it fails or returns empty text, fallback to vision model extraction.
    def _extract_from_image(self, image_bytes: bytes) -> Invoice:
        try:
            text = self._extract_with_ocr(image_bytes)
            if len(text.strip()) >= self.MIN_TEXT_LENGTH:
                return self._parse_with_gpt(text)
        except Exception:
            pass
        
        return self._extract_with_vision(image_bytes)
    
    # Extract text from image using OCR with pytesseract.
    # ref: https://pypi.org/project/pytesseract/
    def _extract_with_ocr(self, image_bytes: bytes) -> str:
        image = Image.open(io.BytesIO(image_bytes))
        text = pytesseract.image_to_string(image)
        return text
    
    # Parse extracted text using GPT-4o with structured JSON format.
    #ref: https://developers.openai.com/api/docs/guides/function-calling
    def _parse_with_gpt(self, text: str) -> Invoice:
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": EXTRACTION_PROMPT + text}],
            response_format={"type": "json_object"},
            temperature=0,
        )

        data = json.loads(response.choices[0].message.content)
        return self._to_invoice(data)
    
    # Extract invoice details using OpenAI vision model. This is a fallback method.
    # ref: https://developers.openai.com/api/docs/guides/vision
    def _extract_with_vision(self, file_bytes: bytes) -> Invoice:
        if not self.client:
            raise ValueError("OpenAI client required for vision extraction")

        # Render first PDF page to JPEG so OpenAI vision can read it
        doc = pymupdf.open(stream=file_bytes, filetype="pdf")
        page = doc[0]
        pix = page.get_pixmap(dpi=150)
        image_bytes = pix.tobytes("jpeg")
        doc.close()

        image_base64 = base64.b64encode(image_bytes).decode()

        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": EXTRACTION_PROMPT},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                ]
            }],
            response_format={"type": "json_object"},
            temperature=0,
        )

        data = json.loads(response.choices[0].message.content)
        return self._to_invoice(data)
    
    # Return invoice data
    def _to_invoice(self, data: dict) -> Invoice:
        
        line_items = [
            LineItem(
                description=item["description"],
                total_amount=float(item["total_amount"]),
                quantity=float(item["quantity"]) if item.get("quantity") else None,
                unit_price=float(item["unit_price"]) if item.get("unit_price") else None,
            )
            for item in data.get("line_items", [])
        ]

        contact_person = None
        if data.get("contact_person"):
            contact_person = Contact(
                name=data["contact_person"].get("name"),
                phone=data["contact_person"].get("phone")
            )
        
        return Invoice(
            invoice_id=data.get("invoice_id") or str(uuid.uuid4()),
            vendor=data.get("vendor", "Unknown"),
            date=data.get("date", ""),
            line_items=line_items,
            vendor_address=self._to_address(data.get("vendor_address")),
            bill_to_name=data.get("bill_to_name"),
            bill_to_address=self._to_address(data.get("bill_to_address")),
            customer_id=data.get("customer_id"),
            due_date=data.get("due_date"),
            contact_person=contact_person,
            tax_exempt=bool(data.get("tax_exempt", False)),
            tax_exempt_reason=data.get("tax_exempt_reason"),
        )
    
    # Return address data
    def _to_address(self, raw: dict | None) -> Address | None:
        if not raw:
            return None
        return Address(
            street=raw.get("street"),
            city=raw.get("city"),
            state=raw.get("state"),
            zip_code=raw.get("zip_code"),
        )
