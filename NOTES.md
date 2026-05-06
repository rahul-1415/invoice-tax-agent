# Development Notes

# Basic Plan (Workflow)
1. User uploads pdf/img on a static frontend hosted on s3.
2. Browser POSTs the file to API Gateway
3. API Gatway invokes the Lambda
4. Lambda detects file type if its an img, it converts it to pdf.
5. InvoiceExtractor - using pymupdf extracts text from the PDF
6. If text is too short (<50 char) - the system uses to GPT 4o vision model to extract information.
7. GPT-4o parses the text into a structured Invoice dataclass.
8. Agent loops through each line item, calls gpt to classify it into a category from the CSV.
9. TaxCalculator computes tax per line item and totals.
10. Results saved to DynamoDB, raw files to S3.
11. JSON response is returned to the browser to display.


# AWS Arch
Browser (S3) -> API Gateway -> Lamdba -
-> OpenAI Tool Call -> DynamoDB (results) -> S3 (raw files)


# AWS Setup Notes
1. DynamoDB setup - Table name: invoice-tax-results, Partition Key: invoice_id
2. S3 Setup - Expire after 90 Days - Bucket Name: invoice-tax-pdfs-661952267320
3. SSM setup - /invoice-agent/openai-api-key
4. IAM setup - Name: invoice-agent-lambda-role
Access to AmazonDynamoDBFullAccess, AmazonS3FullAccess, AmazonSSMReadOnlyAccess, AWSLambdaBasicExecutionRole
5. Lambda Setup - Name: invoice-tax-agent, Role: attached above role. Setup env var.
6. API Gateway Setup - Name: invoice-tax-api
Setup endpoints POST -> /invoices, GET -> /invoices/{invoice_id}, Deployed API. Stored Invoke URL in SSM.
Added GET -> /invoice
7. Setting up CloudFormation


# src/models.py
- Define the dataclasses, data shapes.
- Invoice - line items, addresses, contact, tax exempt status.
- TaxResult - DynamoDB store

# src/invoice_extractor.py
- Text based extraction & Vision extraction.
- Decide based on if text extraction works.
- get_categories() formats all categories to pass to LLM prompt
- get_rate() 

# src/agent.py
- Define OpenAI client, classifier and calculator
- process_invoice() - checks tax exempt first, skips classification if true.
- _classify_line_items() - one GPT-4o call per line item, finds categories.

# src/tax_calculator.py
- Caluclates subtotal().
- calculate_tax() - add taxes.
- calucate() returns TaxResult

# lambda_handler.py
- Initializes clients - cold starts when called.
- DynamoDB doesn't accept Python floats — convert via json.loads(json.dumps(result), parse_float=Decimal)
- GET with invoice_id → fetch one, GET without → scan all