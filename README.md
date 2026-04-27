# Invoice Tax Agent

An AI agent that automates invoice tax classification and calculation.

Upload a PDF or image invoice, the agent extracts line items, classifies each into a tax category using GPT-4o, calculates the tax owed, and stores the result.

## Stack
- OpenAI GPT-4o — invoice extraction and line item classification
- AWS Lambda — backend processing
- AWS API Gateway — REST API
- AWS DynamoDB — stores results
- AWS S3 — stores uploaded files and hosts frontend

## API
- POST /invoices — upload invoice, returns tax result
- GET /invoices — list all processed invoices
- GET /invoices/{invoice_id} — fetch single result

## Setup
```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Tests
```
PYTHONPATH=. pytest tests/unit/ -v -s
```

## Deploy
```
pip install -r requirements.txt -t package/ --platform manylinux2014_x86_64 --only-binary=:all: --python-version 3.12
cp -r src package/ && cp lambda_handler.py tax_rate_by_category.csv package/
cd package && zip -r ../deployment.zip . && cd ..
```
Upload deployment.zip to Lambda via AWS GUI.
