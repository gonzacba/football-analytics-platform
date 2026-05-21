# Lambda function — soccer event processing pipeline
resource "aws_lambda_function" "soccer_pipeline" {
  function_name = "${var.project_name}-pipeline-${var.environment}"
  role          = aws_iam_role.lambda_execution.arn
  handler       = "lambda_function.handler"
  runtime       = "python3.11"
  timeout       = var.lambda_timeout
  memory_size   = var.lambda_memory

  # Code package uploaded to S3
  s3_bucket = aws_s3_bucket.processed_data.id
  s3_key    = "lambda/lambda.zip"

  # Environment variables
  environment {
    variables = {
      OUTPUT_BUCKET = aws_s3_bucket.processed_data.bucket
      ENVIRONMENT   = var.environment
      PROJECT_NAME  = var.project_name
    }
  }

  # Dead-letter queue for failed invocations
  dead_letter_config {
    target_arn = aws_sqs_queue.dead_letter.arn
  }

  # AWS public pandas+pyarrow layer
  layers = [
    "arn:aws:lambda:us-east-1:336392948345:layer:AWSSDKPandas-Python311:24"
  ]

  tags = {
    Project     = var.project_name
    Environment = var.environment
    Component   = "ingestion"
  }
}

# Allow S3 to invoke the Lambda function
resource "aws_lambda_permission" "allow_s3" {
  statement_id  = "AllowS3Invoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.soccer_pipeline.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.raw_events.arn
}

# CloudWatch log group for Lambda logs
resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/${aws_lambda_function.soccer_pipeline.function_name}"
  retention_in_days = 30

  tags = {
    Project     = var.project_name
    Environment = var.environment
  }
}