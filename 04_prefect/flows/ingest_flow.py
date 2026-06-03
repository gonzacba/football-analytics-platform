import json
import boto3
import os
from prefect import flow, task, get_run_logger
from statsbombpy import sb

# Configuration
RAW_BUCKET = "soccer-analytics-raw-events-dev"
REGION = "us-east-1"
COMPETITION_ID = 43   # FIFA World Cup
SEASON_ID = 106       # 2022


@task(name="fetch-matches", retries=2, retry_delay_seconds=10)
def fetch_matches(competition_id: int, season_id: int) -> list:
    """Fetch available matches from StatsBomb open data."""
    logger = get_run_logger()
    logger.info(f"Fetching matches for competition {competition_id}, season {season_id}")
    matches = sb.matches(competition_id=competition_id, season_id=season_id)
    match_list = matches[["match_id", "home_team", "away_team"]].to_dict("records")
    logger.info(f"Found {len(match_list)} matches")
    return match_list


@task(name="fetch-events", retries=2, retry_delay_seconds=10)
def fetch_events(match: dict) -> dict:
    """Fetch events for a single match."""
    logger = get_run_logger()
    match_id = match["match_id"]
    logger.info(f"Fetching events for match {match_id}: {match['home_team']} vs {match['away_team']}")
    events = sb.events(match_id=match_id)
    events_json = json.loads(events.to_json(orient="records"))
    logger.info(f"Fetched {len(events_json)} events")
    return {"match_id": match_id, "events": events_json}


@task(name="upload-to-s3", retries=3, retry_delay_seconds=5)
def upload_to_s3(match_data: dict, bucket: str) -> str:
    """Upload match events JSON to S3 raw bucket."""
    logger = get_run_logger()
    match_id = match_data["match_id"]
    key = f"raw/match_{match_id}.json"

    s3 = boto3.client("s3", region_name=REGION)
    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=json.dumps(match_data["events"]),
        ContentType="application/json"
    )
    logger.info(f"Uploaded to s3://{bucket}/{key}")
    return key


@task(name="verify-upload")
def verify_upload(key: str, bucket: str) -> bool:
    """Verify the file was successfully uploaded to S3."""
    logger = get_run_logger()
    s3 = boto3.client("s3", region_name=REGION)
    try:
        response = s3.head_object(Bucket=bucket, Key=key)
        size = response["ContentLength"]
        logger.info(f"Verified: {key} ({size} bytes)")
        return True
    except Exception as e:
        logger.error(f"Verification failed: {e}")
        return False


@flow(name="soccer-ingest-flow", log_prints=True)
def ingest_flow(
    competition_id: int = COMPETITION_ID,
    season_id: int = SEASON_ID,
    max_matches: int = 5,
    bucket: str = RAW_BUCKET
):
    """
    Main ingestion flow.
    Fetches StatsBomb match data and uploads to S3 raw bucket.
    Triggers the Lambda processing pipeline automatically via S3 event.
    """
    logger = get_run_logger()
    logger.info(f"Starting ingestion flow for {max_matches} matches")

    # Fetch available matches
    matches = fetch_matches(competition_id, season_id)
    matches = matches[:max_matches]

    # Process each match
    uploaded_keys = []
    for match in matches:
        events_data = fetch_events(match)
        key = upload_to_s3(events_data, bucket)
        verified = verify_upload(key, bucket)
        if verified:
            uploaded_keys.append(key)

    logger.info(f"Ingestion complete. Uploaded {len(uploaded_keys)}/{len(matches)} matches")
    return uploaded_keys


if __name__ == "__main__":
    ingest_flow(max_matches=3)