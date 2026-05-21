# Dead-letter queue — catches failed pipeline events
# If Lambda fails to process a file, the event goes here
# instead of disappearing silently
resource "aws_sqs_queue" "dead_letter" {
  name                      = "${var.project_name}-dlq-${var.environment}"
  message_retention_seconds = 1209600 # 14 days

  tags = {
    Project     = var.project_name
    Environment = var.environment
    Component   = "reliability"
  }
}

# Main processing queue — buffers incoming events
resource "aws_sqs_queue" "pipeline_queue" {
  name                       = "${var.project_name}-pipeline-${var.environment}"
  visibility_timeout_seconds = 120
  message_retention_seconds  = 86400 # 1 day

  # Point failed messages to dead-letter queue
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dead_letter.arn
    maxReceiveCount     = 3 # retry 3 times before sending to DLQ
  })

  tags = {
    Project     = var.project_name
    Environment = var.environment
    Component   = "ingestion"
  }
}

# CloudWatch alarm — alerts when dead-letter queue has messages
resource "aws_cloudwatch_metric_alarm" "dlq_alarm" {
  alarm_name          = "${var.project_name}-dlq-not-empty-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = 300
  statistic           = "Sum"
  threshold           = 0
  alarm_description   = "Dead-letter queue has messages — pipeline failures detected"

  dimensions = {
    QueueName = aws_sqs_queue.dead_letter.name
  }

  tags = {
    Project     = var.project_name
    Environment = var.environment
  }
}