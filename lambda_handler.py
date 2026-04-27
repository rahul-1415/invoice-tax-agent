import os
import io
import json
import base64
import boto3
from PIL import Image
from decimal import Decimal
from datetime import datetime, timezone
from openai import OpenAI
from src.invoice_extractor import InvoiceExtractor
from src.tax_classifier import TaxClassifier
from src.tax_calculator import TaxCalculator
from src.agent import Agent

# Setting up environment variables and clients.
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
DYNAMODB_TABLE = os.environ["DYNAMODB_TABLE"]
S3_BUCKET = os.environ["S3_BUCKET"]
TAX_RATES_CSV_PATH = os.environ.get("TAX_RATES_CSV_PATH", "tax_rate_by_category.csv")
REGION = os.environ.get("AWS_REGION", "us-east-1")

openai_client = OpenAI(api_key=OPENAI_API_KEY)
dynamodb = boto3.resource("dynamodb", region_name=REGION)
table = dynamodb.Table(DYNAMODB_TABLE)
s3 = boto3.client("s3", region_name=REGION)

extractor = InvoiceExtractor(openai_client)
classifier = TaxClassifier(TAX_RATES_CSV_PATH)
calculator = TaxCalculator()
agent = Agent(openai_client, classifier, calculator)

# CORS headers for API Gateway
CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "OPTIONS,POST,GET",
}

# Helper function to format HTTP responses, fix: ensure Decimal types from DynamoDB are converted to string.
def _response(status: int, body: dict) -> dict:
    return {
        "statusCode": status,
        "headers": {**CORS_HEADERS, "Content-Type": "application/json"},
        "body": json.dumps(body, default=str),
    }

# POST /invoices — accept invoice files, extract, classify, calculate.
def _handle_post(event: dict) -> dict:
    body = event.get("body", "")
    is_base64 = event.get("isBase64Encoded", False)

    if not body:
        return _response(400, {"error": "Empty request body"})

    file_bytes = base64.b64decode(body) if is_base64 else body.encode()

    # fix: Convert images to PDF for consistent processing, it gets complicated when passing to API gateway with different content types.
    if file_bytes[:4] != b"%PDF":
        image = Image.open(io.BytesIO(file_bytes))
        buf = io.BytesIO()
        image.convert("RGB").save(buf, format="PDF")
        file_bytes = buf.getvalue()

    invoice = extractor.extract(file_bytes, "pdf")
    result = agent.process_invoice(invoice, extraction_method="pdf")
    result["processed_at"] = datetime.now(timezone.utc).isoformat()

    # DynamoDB requires Decimal instead of float
    dynamo_item = json.loads(json.dumps(result), parse_float=Decimal)

    table.put_item(Item=dynamo_item)

    s3.put_object(
        Bucket=S3_BUCKET,
        Key=f"invoices/{result['invoice_id']}.pdf",
        Body=file_bytes,
        ContentType="application/pdf",
    )

    return _response(200, result)


# GET /invoices — list all processed invoices from DynamoDB
def _handle_list() -> dict:
    resp = table.scan()
    return _response(200, resp.get("Items", []))


# GET /invoices/{invoice_id} — fetch single result from DynamoDB
def _handle_get(event: dict) -> dict:
    invoice_id = (event.get("pathParameters") or {}).get("invoice_id")
    if not invoice_id:
        return _response(400, {"error": "Missing invoice_id"})

    resp = table.get_item(Key={"invoice_id": invoice_id})
    item = resp.get("Item")
    if not item:
        return _response(404, {"error": f"Invoice {invoice_id} not found"})

    return _response(200, item)

# Lambda handler entry point
def lambda_handler(event: dict, context) -> dict:
    method = event.get("httpMethod", "")

    if method == "OPTIONS":
        return _response(200, {})
    elif method == "POST":
        return _handle_post(event)
    elif method == "GET":
        invoice_id = (event.get("pathParameters") or {}).get("invoice_id")
        return _handle_get(event) if invoice_id else _handle_list()
    else:
        return _response(405, {"error": f"Method {method} not allowed"})
