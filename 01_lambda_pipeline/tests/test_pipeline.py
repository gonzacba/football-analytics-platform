import json
import boto3
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../src"))

from moto import mock_aws
from unittest.mock import patch
from transformer import load_events_from_json, to_parquet_bytes
from validator import validate_events

SAMPLE_EVENTS = [
    {
        "id": "abc123",
        "index": 1,
        "period": 1,
        "timestamp": "00:00:01.000",
        "type": {"name": "Pass"},
        "team": {"name": "Inter Miami CF"},
        "player": {"name": "Lionel Messi"},
        "location": [60.0, 40.0]
    }
]

def test_transform_returns_dataframe():
    df = load_events_from_json(SAMPLE_EVENTS)
    assert len(df) == 1
    assert "type" in df.columns
    assert "team" in df.columns

def test_validation_passes_on_good_data():
    df = load_events_from_json(SAMPLE_EVENTS)
    validated = validate_events(df)
    assert validated is not None

def test_parquet_serialization():
    df = load_events_from_json(SAMPLE_EVENTS)
    parquet_bytes = to_parquet_bytes(df)
    assert len(parquet_bytes) > 0

@mock_aws
def test_lambda_handler_end_to_end():
    """Full pipeline test with mocked S3."""
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket="football-raw-data")
    s3.create_bucket(Bucket="football-processed-data")

    s3.put_object(
        Bucket="football-raw-data",
        Key="raw/match_001.json",
        Body=json.dumps(SAMPLE_EVENTS)
    )

    s3_event = {
        "Records": [{
            "s3": {
                "bucket": {"name": "football-raw-data"},
                "object": {"key": "raw/match_001.json"}
            }
        }]
    }

    with patch.dict(os.environ, {"OUTPUT_BUCKET": "football-processed-data"}):
        from lambda_function import handler
        result = handler(s3_event, {})

    assert result["statusCode"] == 200

    objects = s3.list_objects_v2(Bucket="football-processed-data")
    assert objects["KeyCount"] == 1