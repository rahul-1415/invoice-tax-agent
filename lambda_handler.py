import os
import json
import base64
import boto3
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

# Helper function to format HTTP responses
def _response(status: int, body: dict) -> dict:
    return {
        "statusCode": status,
        "headers": {**CORS_HEADERS, "Content-Type": "application/json"},
        "body": json.dumps(body),
    }

# POST /invoices — accept invoice files, extract, classify, calculate.
def _handle_post(event: dict) -> dict:
    body = event.get("body", "")
    is_base64 = event.get("isBase64Encoded", False)

    if not body:
        return _response(400, {"error": "Empty request body"})

    file_bytes = base64.b64decode(body) if is_base64 else body.encode()

    file_type = "pdf" if file_bytes[:4] == b"%PDF" else "image"

    invoice = extractor.extract(file_bytes, file_type)
    result = agent.process_invoice(invoice, extraction_method=file_type)
    result["processed_at"] = datetime.now(timezone.utc).isoformat()

    # Store result
    table.put_item(Item=result)

    # Store original file
    content_type = "application/pdf" if file_type == "pdf" else "image/jpeg"
    extension = "pdf" if file_type == "pdf" else "jpg"
    s3.put_object(
        Bucket=S3_BUCKET,
        Key=f"invoices/{result['invoice_id']}.{extension}",
        Body=file_bytes,
        ContentType=content_type,
    )

    return _response(200, result)


# GET /invoices/{invoice_id} — fetch result from DynamoDB
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
        return _handle_get(event)
    else:
        return _response(405, {"error": f"Method {method} not allowed"})
