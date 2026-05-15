# Football Analytics Data Pipeline

An event-driven AWS data pipeline that ingests StatsBomb match event data, validates schema integrity, and transforms raw JSON into optimized Parquet format for analytics.

Built as a demonstration of the core data engineering patterns used in professional football analytics infrastructure.

## Architecture

StatsBomb JSON (3,900+ events per match)
        down
S3 Raw Bucket (s3://football-raw-events/raw/)
        down (S3 event trigger)
AWS Lambda (Python 3.11)
        down
Pandera Schema Validation
        down
Pandas + PyArrow Transformation (JSON to Parquet)
        down
S3 Processed Bucket (s3://football-processed/processed/)

## Tech Stack

- Cloud: AWS Lambda, S3, IAM, CloudWatch
- Data Processing: Pandas, PyArrow, Pandera
- Output Format: Parquet (columnar, optimized for Athena queries)
- Testing: pytest, moto (AWS mocking)
- Data Source: StatsBomb Open Data (real match events)
- Infrastructure: boto3, deployed via Python scripts

## Project Structure

01_lambda_pipeline/
├── src/
│   ├── lambda_function.py    # Lambda handler, S3 trigger logic
│   ├── transformer.py        # JSON flattening, Parquet serialization
│   └── validator.py          # Pandera schema enforcement
├── tests/
│   └── test_pipeline.py      # Unit + integration tests with moto
├── infra/
│   ├── setup_aws.py          # Full deployment script
│   ├── cleanup_aws.py        # Teardown script
│   └── test_live.py          # Live pipeline test with real data
└── README.md

## Pipeline Details

### Ingestion
Raw StatsBomb match event JSON files are uploaded to the S3 raw bucket under the raw/ prefix. Each upload automatically triggers the Lambda function via S3 event notification.

### Validation
Pandera enforces a strict schema on every incoming dataset:
- Column presence and types (id, index, period, timestamp, type, team, player)
- Value constraints (period must be 1-5)
- Null checks per field

Invalid data raises a SchemaError before anything is written downstream.

### Transformation
pd.json_normalize() flattens nested StatsBomb JSON structures. Columns are standardized, renamed, and cast to correct types. The clean DataFrame is serialized to Parquet using PyArrow for efficient downstream querying.

### Output
Processed Parquet files are written to the processed bucket mirroring the input path:
- Input:  raw/match_9880.json
- Output: processed/match_9880.parquet

A single match (3,947 events) compresses from raw JSON to ~215 KB Parquet.

## Test Suite

4 tests covering the full pipeline:

    conda activate football-pipeline
    pytest tests/ -v

| Test                            | Type        | Description                                  |
|---------------------------------|-------------|----------------------------------------------|
| test_transform_returns_dataframe | Unit       | Verifies JSON flattening and column mapping  |
| test_validation_passes_on_good_data | Unit    | Verifies Pandera schema acceptance           |
| test_parquet_serialization      | Unit        | Verifies PyArrow byte output                 |
| test_lambda_handler_end_to_end  | Integration | Full pipeline with mocked S3 via moto        |

## Deployment

    conda activate football-pipeline
    python infra/setup_aws.py
    python infra/test_live.py
    python infra/cleanup_aws.py

## Data Source

Uses StatsBomb Open Data (https://github.com/statsbomb/open-data) — freely available professional match data including La Liga, Champions League, and World Cup events. StatsBomb is one of the leading football data providers used by professional clubs worldwide.