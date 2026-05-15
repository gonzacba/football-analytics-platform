import boto3
import json
import time
from statsbombpy import sb

REGION = "us-east-1"
RAW_BUCKET = "football-raw-events-gonvi"
PROCESSED_BUCKET = "football-processed-gonvi"

# Get a real match from StatsBomb free data
print("Fetching StatsBomb free data...")
matches = sb.matches(competition_id=11, season_id=1)  # La Liga 2005/06
match_id = matches.iloc[0]["match_id"]
print(f"Using match_id: {match_id}")

events = sb.events(match_id=match_id)
events_json = json.loads(events.to_json(orient="records"))
print(f"Loaded {len(events_json)} events")

# Upload to raw bucket
s3 = boto3.client("s3", region_name=REGION)
key = f"raw/match_{match_id}.json"
s3.put_object(
    Bucket=RAW_BUCKET,
    Key=key,
    Body=json.dumps(events_json),
    ContentType="application/json"
)
print(f"✓ Uploaded to s3://{RAW_BUCKET}/{key}")
print("Waiting for Lambda to process...")
time.sleep(10)

# Check if processed file appeared
result = s3.list_objects_v2(Bucket=PROCESSED_BUCKET, Prefix="processed/")
if result.get("KeyCount", 0) > 0:
    for obj in result["Contents"]:
        print(f"✓ Processed file found: {obj['Key']} ({obj['Size']} bytes)")
else:
    print("No processed files yet - check CloudWatch logs")
    print("Run: aws logs tail /aws/lambda/football-event-pipeline --follow")