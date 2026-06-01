import time
from prefect import flow, task, get_run_logger
from ingest_flow import ingest_flow
from transform_flow import transform_flow


@task(name="wait-for-lambda", retries=3, retry_delay_seconds=15)
def wait_for_lambda_processing(uploaded_keys: list, wait_seconds: int = 30) -> bool:
    """
    Wait for Lambda to process uploaded files.
    Lambda is triggered automatically by S3 events.
    """
    logger = get_run_logger()
    logger.info(f"Waiting {wait_seconds}s for Lambda to process {len(uploaded_keys)} files...")
    time.sleep(wait_seconds)
    logger.info("Wait complete — Lambda should have processed all files")
    return True


@task(name="verify-processed-files")
def verify_processed_files(uploaded_keys: list, processed_bucket: str) -> dict:
    """Verify Lambda successfully created Parquet files in processed bucket."""
    import boto3
    logger = get_run_logger()
    s3 = boto3.client("s3", region_name="us-east-1")

    results = {"success": [], "missing": []}

    for raw_key in uploaded_keys:
        processed_key = raw_key.replace("raw/", "processed/").replace(".json", ".parquet")
        try:
            response = s3.head_object(Bucket=processed_bucket, Key=processed_key)
            size = response["ContentLength"]
            logger.info(f"Found: {processed_key} ({size} bytes)")
            results["success"].append(processed_key)
        except Exception:
            logger.warning(f"Missing: {processed_key}")
            results["missing"].append(processed_key)

    success_rate = len(results["success"]) / len(uploaded_keys) * 100
    logger.info(f"Processing success rate: {success_rate:.1f}%")
    return results


@flow(name="soccer-analytics-pipeline", log_prints=True)
def pipeline_flow(
    competition_id: int = 11,
    season_id: int = 1,
    max_matches: int = 3,
    raw_bucket: str = "soccer-analytics-raw-events-dev",
    processed_bucket: str = "soccer-analytics-processed-dev",
    run_tests: bool = True
):
    """
    Full end-to-end soccer analytics pipeline flow.

    Steps:
    1. Ingest: fetch StatsBomb data and upload to S3
    2. Wait: allow Lambda to process files automatically
    3. Verify: confirm Parquet files exist in processed bucket
    4. Transform: run dbt models and tests
    """
    logger = get_run_logger()
    logger.info("=" * 50)
    logger.info("Soccer Analytics Pipeline Starting")
    logger.info("=" * 50)

    # Step 1 — Ingest
    logger.info("Step 1: Ingesting match data...")
    uploaded_keys = ingest_flow(
        competition_id=competition_id,
        season_id=season_id,
        max_matches=max_matches,
        bucket=raw_bucket
    )
    logger.info(f"Ingested {len(uploaded_keys)} matches")

    # Step 2 — Wait for Lambda
    logger.info("Step 2: Waiting for Lambda processing...")
    wait_for_lambda_processing(uploaded_keys, wait_seconds=30)

    # Step 3 — Verify
    logger.info("Step 3: Verifying processed files...")
    verification = verify_processed_files(uploaded_keys, processed_bucket)
    logger.info(f"Verified: {len(verification['success'])} success, {len(verification['missing'])} missing")

    # Step 4 — Transform
    logger.info("Step 4: Running dbt transformations...")
    transform_result = transform_flow(run_tests=run_tests)
    logger.info(f"Transformation status: {transform_result['status']}")

    logger.info("=" * 50)
    logger.info("Pipeline Complete")
    logger.info("=" * 50)

    return {
        "ingested": len(uploaded_keys),
        "processed": len(verification["success"]),
        "missing": len(verification["missing"]),
        "transform_status": transform_result["status"]
    }


if __name__ == "__main__":
    pipeline_flow(max_matches=3)