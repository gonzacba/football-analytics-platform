# Soccer Analytics Platform — Terraform Infrastructure

Complete AWS infrastructure for the soccer analytics platform, provisioned as code using Terraform.

## What This Provisions

```
AWS Infrastructure
├── S3 Buckets
│   ├── soccer-analytics-raw-events-dev      # incoming JSON from data providers
│   └── soccer-analytics-processed-dev       # cleaned Parquet files for analytics
├── Lambda
│   └── soccer-analytics-pipeline-dev        # event processing function
├── IAM
│   ├── soccer-analytics-lambda-role-dev     # execution role
│   └── soccer-analytics-lambda-policy-dev  # least-privilege permissions
├── SQS
│   ├── soccer-analytics-pipeline-dev        # main processing queue
│   └── soccer-analytics-dlq-dev            # dead-letter queue for failures
└── CloudWatch
    ├── log group                            # Lambda logs, 30-day retention
    └── metric alarm                         # fires when DLQ receives messages
```

## File Structure

```
03_terraform/
├── main.tf        # provider config and AWS caller identity
├── variables.tf   # configurable inputs (region, environment, project name)
├── s3.tf          # buckets, public access blocks, lifecycle rules, S3 trigger
├── iam.tf         # execution role and least-privilege policy
├── sqs.tf         # pipeline queue, dead-letter queue, CloudWatch alarm
├── lambda.tf      # function, S3 permission, log group
└── outputs.tf     # exported resource names and ARNs
```

## Key Design Decisions

### Least-Privilege IAM
The Lambda role only has permission to read from the raw bucket, write to the processed bucket, send to SQS, and write CloudWatch logs. No wildcard permissions.

### Dead-Letter Queue
Failed Lambda invocations are routed to the DLQ instead of disappearing silently. A CloudWatch alarm fires immediately when the DLQ receives any message — ensuring pipeline failures are visible.

### S3 Lifecycle Management
Processed Parquet files automatically transition to STANDARD_IA after 90 days and GLACIER after 365 days — reducing storage costs as data ages.

### Security
Both S3 buckets block all public access. No data is publicly accessible.

## Usage

```
terraform init
terraform plan
terraform apply
terraform destroy
```

## Variables

| Variable | Default | Description |
|---|---|---|
| aws_region | us-east-1 | AWS region |
| project_name | soccer-analytics | Used for all resource names |
| environment | dev | Environment tag (dev/prod) |
| lambda_timeout | 60 | Lambda timeout in seconds |
| lambda_memory | 512 | Lambda memory in MB |

## Outputs

| Output | Description |
|---|---|
| raw_bucket_name | S3 bucket for incoming JSON |
| processed_bucket_name | S3 bucket for Parquet output |
| lambda_function_name | Lambda function name |
| lambda_function_arn | Lambda function ARN |
| dead_letter_queue_url | DLQ URL for monitoring |
| pipeline_queue_url | Main pipeline queue URL |
| cloudwatch_log_group | Lambda log group path |