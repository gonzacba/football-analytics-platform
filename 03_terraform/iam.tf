# Trust policy — allows Lambda to assume this role
data "aws_iam_policy_document" "lambda_trust" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

# IAM role for Lambda execution
resource "aws_iam_role" "lambda_execution" {
  name               = "${var.project_name}-lambda-role-${var.environment}"
  assume_role_policy = data.aws_iam_policy_document.lambda_trust.json

  tags = {
    Project     = var.project_name
    Environment = var.environment
  }
}

# Policy — what the Lambda is allowed to do
data "aws_iam_policy_document" "lambda_permissions" {
  # Read from raw bucket
  statement {
    effect  = "Allow"
    actions = ["s3:GetObject", "s3:ListBucket"]
    resources = [
      aws_s3_bucket.raw_events.arn,
      "${aws_s3_bucket.raw_events.arn}/*"
    ]
  }

  # Write to processed bucket
  statement {
    effect  = "Allow"
    actions = ["s3:PutObject", "s3:GetObject", "s3:ListBucket"]
    resources = [
      aws_s3_bucket.processed_data.arn,
      "${aws_s3_bucket.processed_data.arn}/*"
    ]
  }

  # Write logs to CloudWatch
  statement {
    effect = "Allow"
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents"
    ]
    resources = ["arn:aws:logs:*:*:*"]
  }

  # Send failed messages to SQS dead-letter queue
  statement {
    effect    = "Allow"
    actions   = ["sqs:SendMessage"]
    resources = [aws_sqs_queue.dead_letter.arn]
  }
}

resource "aws_iam_policy" "lambda_permissions" {
  name   = "${var.project_name}-lambda-policy-${var.environment}"
  policy = data.aws_iam_policy_document.lambda_permissions.json
}

resource "aws_iam_role_policy_attachment" "lambda_permissions" {
  role       = aws_iam_role.lambda_execution.name
  policy_arn = aws_iam_policy.lambda_permissions.arn
}