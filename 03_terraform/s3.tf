# Raw events bucket — receives incoming JSON from data providers
resource "aws_s3_bucket" "raw_events" {
  bucket = "${var.project_name}-raw-events-${var.environment}"

  tags = {
    Project     = var.project_name
    Environment = var.environment
    Component   = "ingestion"
  }
}

# Processed data bucket — stores cleaned Parquet files
resource "aws_s3_bucket" "processed_data" {
  bucket = "${var.project_name}-processed-${var.environment}"

  tags = {
    Project     = var.project_name
    Environment = var.environment
    Component   = "processed"
  }
}

# Block all public access on both buckets
resource "aws_s3_bucket_public_access_block" "raw_events" {
  bucket                  = aws_s3_bucket.raw_events.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_public_access_block" "processed_data" {
  bucket                  = aws_s3_bucket.processed_data.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Lifecycle rule — move processed files to cheaper storage after 90 days
resource "aws_s3_bucket_lifecycle_configuration" "processed_data" {
  bucket = aws_s3_bucket.processed_data.id

  rule {
    id     = "archive-old-parquet"
    status = "Enabled"

    filter {
      prefix = ""
    }

    transition {
      days          = 90
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = 365
      storage_class = "GLACIER"
    }
  }
}

# S3 notification to trigger Lambda when JSON lands in raw/
resource "aws_s3_bucket_notification" "raw_events_trigger" {
  bucket = aws_s3_bucket.raw_events.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.soccer_pipeline.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "raw/"
    filter_suffix       = ".json"
  }

  depends_on = [aws_lambda_permission.allow_s3]
}