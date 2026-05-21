output "raw_bucket_name" {
  description = "Name of the raw events S3 bucket"
  value       = aws_s3_bucket.raw_events.bucket
}

output "processed_bucket_name" {
  description = "Name of the processed data S3 bucket"
  value       = aws_s3_bucket.processed_data.bucket
}

output "lambda_function_name" {
  description = "Name of the Lambda function"
  value       = aws_lambda_function.soccer_pipeline.function_name
}

output "lambda_function_arn" {
  description = "ARN of the Lambda function"
  value       = aws_lambda_function.soccer_pipeline.arn
}

output "dead_letter_queue_url" {
  description = "URL of the dead-letter queue"
  value       = aws_sqs_queue.dead_letter.url
}

output "pipeline_queue_url" {
  description = "URL of the main pipeline queue"
  value       = aws_sqs_queue.pipeline_queue.url
}

output "cloudwatch_log_group" {
  description = "CloudWatch log group for Lambda"
  value       = aws_cloudwatch_log_group.lambda_logs.name
}