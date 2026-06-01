# Soccer Analytics Platform — Prefect Orchestration

Workflow orchestration layer for the soccer analytics platform. Coordinates data ingestion, Lambda processing, and dbt transformation as an automated end-to-end pipeline.

## Architecture

```
Prefect Pipeline Flow
        |
        |-- Step 1: Ingest Flow
        |       |-- fetch_matches (StatsBomb API)
        |       |-- fetch_events (per match)
        |       |-- upload_to_s3 (raw bucket)
        |       |-- verify_upload (confirm S3 receipt)
        |
        |-- Step 2: Wait for Lambda
        |       |-- Lambda auto-triggered by S3 event
        |       |-- Pandera validation
        |       |-- JSON to Parquet transformation
        |
        |-- Step 3: Verify Processed Files
        |       |-- Confirm Parquet files exist in processed bucket
        |       |-- Report success rate
        |
        |-- Step 4: Transform Flow
                |-- dbt run (5 models)
                |-- dbt test (12 tests)
```

## Flow Structure

```
04_prefect/
└── flows/
    ├── ingest_flow.py      # StatsBomb fetch + S3 upload
    ├── transform_flow.py   # dbt run + test orchestration
    └── pipeline_flow.py    # full end-to-end pipeline
```

## Key Prefect Concepts Used

### Tasks
Each unit of work is a @task with retry logic:
- fetch_matches: retries=2, retry_delay=10s
- fetch_events: retries=2, retry_delay=10s
- upload_to_s3: retries=3, retry_delay=5s
- dbt_run: retries=1, retry_delay=30s

### Flows
Each flow is a @flow that orchestrates tasks:
- ingest_flow: handles all ingestion steps
- transform_flow: handles all dbt steps
- pipeline_flow: parent flow that calls both as subflows

### Subflows
pipeline_flow calls ingest_flow and transform_flow as subflows. Prefect tracks each subflow run independently with its own logs and state.

## Live Run Results

Full end-to-end pipeline verified:

```
Step 1 — Ingestion:    3/3 matches uploaded (11,767 events)
Step 2 — Lambda:       JSON to Parquet via AWS Lambda
Step 3 — Verification: 3/3 Parquet files confirmed (avg ~218 KB each)
Step 4 — Transform:    5/5 dbt models, 12/12 tests passing
```

## Running the Flows

First deploy the AWS infrastructure:
```
cd 03_terraform
terraform apply
cd ../01_lambda_pipeline
python ../03_terraform/upload_lambda.py
```

Then run the flows:
```
conda activate football-pipeline
cd 04_prefect/flows

# Run individual flows
python ingest_flow.py
python transform_flow.py

# Run full pipeline
python pipeline_flow.py
```

Tear down AWS when done:
```
cd 03_terraform
aws s3 rm s3://soccer-analytics-raw-events-dev --recursive
aws s3 rm s3://soccer-analytics-processed-dev --recursive
terraform destroy
```

## Why Prefect?

Without orchestration, every pipeline step runs manually. Prefect adds:
- Automatic retries on failure
- Task-level logging and observability
- Subflow dependency management
- Ready for scheduled deployment (Prefect Cloud or self-hosted server)
- Clear success/failure states per task and flow

In production, pipeline_flow would run on a schedule after every match, automatically ingesting new data, waiting for Lambda processing, and refreshing dbt models — with no manual intervention.

## Connection to Full Platform

This is the orchestration layer of a 4-component platform:

01_lambda_pipeline  ->  AWS event-driven ingestion
02_dbt_models       ->  Analytics transformation layer
03_terraform        ->  Infrastructure as code
04_prefect          ->  Workflow orchestration (this folder)
