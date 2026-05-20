import json
import boto3
import os
import logging
from transformer import load_events_from_json, to_parquet_bytes
from validator import validate_events

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client("s3")
OUTPUT_BUCKET = os.environ.get("OUTPUT_BUCKET", "soccer-processed-data")

def handler(event, context):
    """
    Lambda handler triggered by S3 PUT event.
    Reads raw JSON match events, validates, transforms, writes Parquet.
    """
    for record in event["Records"]:
        input_bucket = record["s3"]["bucket"]["name"]
        input_key = record["s3"]["object"]["key"]

        logger.info(f"Processing: s3://{input_bucket}/{input_key}")

        # Read raw JSON from S3
        response = s3_client.get_object(Bucket=input_bucket, Key=input_key)
        raw_data = json.loads(response["Body"].read().decode("utf-8"))

        # Transform
        df = load_events_from_json(raw_data)
        logger.info(f"Loaded {len(df)} events")

        # Validate
        validated_df = validate_events(df)
        logger.info("Schema validation passed")

        # Write Parquet to output bucket
        output_key = input_key.replace("raw/", "processed/").replace(".json", ".parquet")
        parquet_bytes = to_parquet_bytes(validated_df)

        s3_client.put_object(
            Bucket=OUTPUT_BUCKET,
            Key=output_key,
            Body=parquet_bytes,
            ContentType="application/octet-stream"
        )

        logger.info(f"Written to s3://{OUTPUT_BUCKET}/{output_key}")

    return {"statusCode": 200, "body": "Pipeline complete"}