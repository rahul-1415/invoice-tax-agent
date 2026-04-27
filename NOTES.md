# Development Notes

# AWS Setup Notes
1. DynamoDB setup - Table name: invoice-tax-results, Partition Key: invoice_id
2. S3 Setup - Expire after 90 Days - Bucket Name: invoice-tax-pdfs-661952267320
3. SSM setup - /invoice-agent/openai-api-key
4. IAM setup - Name: invoice-agent-lambda-role
Access to AmazonDynamoDBFullAccess, AmazonS3FullAccess, AmazonSSMReadOnlyAccess, AWSLambdaBasicExecutionRole
5. Lambda Setup - Name: invoice-tax-agent, Role: attached above role. Setup env var.
6. API Gateway Setup - Name: invoice-tax-api
Setup endpoints POST -> /invoices, GET -> /invoices/{invoice_id}, Deployed API. Stored Invoke URL in SSM.