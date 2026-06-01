# Soccer Analytics — dbt Transformation Layer

A dbt (data build tool) project that transforms raw StatsBomb match event data into analytics-ready tables for player performance, team analysis, and shot intelligence.

This project sits on top of the AWS Lambda ingestion pipeline (see 01_lambda_pipeline) and represents the transformation layer of the soccer analytics platform.

## Architecture

```
S3 Processed Bucket (Parquet files from Lambda pipeline)
        |
DuckDB (local analytical engine reads Parquet directly)
        |
dbt Transformation Layer
        |
    base_events (raw Parquet loaded into DuckDB)
        |
    stg_events (cleaned, renamed, typed — staging layer)
        |
    ┌───────────────────────────────────┐
    │               │                   │
mart_player_    mart_team_        mart_shot_
performance     summary           analysis
(per player     (per team         (individual
 per match)      per match)        shots)
```

## Tech Stack

- Transformation: dbt Core 1.11
- Database Engine: DuckDB (reads Parquet natively)
- Data Format: Parquet (from Day 1 Lambda pipeline)
- Data Source: StatsBomb Open Data (10 La Liga matches, 38,382 events)
- Testing: dbt built-in tests (unique, not_null, accepted_values)

## Project Structure

```
02_dbt_models/
├── models/
│   ├── staging/
│   │   ├── base_events.sql
│   │   ├── stg_events.sql
│   │   ├── sources.yml
│   │   └── schema.yml
│   └── marts/
│       ├── mart_player_performance.sql
│       ├── mart_team_summary.sql
│       ├── mart_shot_analysis.sql
│       └── schema.yml
├── data/
│   ├── events.parquet
│   └── download_data.py
├── dbt_project.yml
└── README.md
```

## The 3-Layer Model Architecture

### Layer 1 — Base (base_events)
Loads the raw Parquet file directly into DuckDB using read_parquet(). No transformations — just makes the data available to dbt.

### Layer 2 — Staging (stg_events)
Cleans and standardizes the raw data:
- Renames columns to consistent snake_case names
- Selects only the columns needed for analytics
- Casts to correct data types
- Adds clear descriptions for every field

This layer is materialized as a view — it adds no storage cost and always reflects the latest base data.

### Layer 3 — Marts
Business-logic models that analysts actually query. Materialized as tables for fast query performance.

## Models

### mart_player_performance
Aggregates per player per match:
- Passing: total passes, completed passes, pass completion %, avg pass length, goal assists, shot assists, crosses, through balls
- Shooting: total shots, goals, shots on target, total xG, avg xG per shot, first-time shots, one-on-ones
- Dribbling: total dribbles, successful dribbles, dribble success %

### mart_team_summary
Aggregates per team per match:
- Passing volume and completion rate
- Shot counts and goals
- Expected goals (xG)
- Pressing intensity (total pressures)
- Home vs Away context

### mart_shot_analysis
Individual shot records enriched with context:
- Shot outcome, body part, technique, type
- xG value per shot
- Boolean flags: is_goal, is_on_target, is_first_time, is_one_on_one, is_open_goal, is_under_pressure
- Time bracket (0-15, 15-30, 30-45, 45-60, 60-75, 75+)

## Sample Results (10 La Liga Matches)

### Top Players by Passes
```
Player                              Team        Passes  Completion%  Goals  xG
Sergio Busquets i Burgos            Barcelona   639     89.6%        1      0.25
Lionel Andrés Messi Cuccittini      Barcelona   578     79.7%        13     8.96
Ivan Rakitić                        Barcelona   510     89.3%        0      0.30
Gerard Piqué Bernabéu               Barcelona   476     89.1%        0      0.65
Jordi Alba Ramos                    Barcelona   469     86.2%        1      0.68
```

### Team Summary
```
Team                    Passes  Completion%  Shots  Goals  xG
Barcelona               6367    86.4%        142    28     20.40
RC Deportivo La Coruña  451     81.8%        17     2      2.24
Real Madrid             580     89.3%        17     2      1.77
```

### Shots by Time Bracket
```
Period   Shots  Goals  Avg xG
0-15     38     6      0.115
15-30    46     5      0.118
30-45    44     5      0.087
45-60    49     8      0.098
60-75    38     4      0.114
75+      61     8      0.155
```

## Test Suite

12 dbt tests covering all models:

```
dbt test
```

| Test | Model | Type |
|------|-------|------|
| unique | stg_events.event_id | Uniqueness |
| not_null | stg_events.event_id | Null check |
| not_null | stg_events.match_id | Null check |
| not_null | stg_events.event_type | Null check |
| not_null | stg_events.period | Null check |
| accepted_values | stg_events.period [1-5] | Value check |
| unique | mart_shot_analysis.event_id | Uniqueness |
| not_null | mart_shot_analysis.event_id | Null check |
| not_null | mart_player_performance.player_name | Null check |
| not_null | mart_player_performance.match_id | Null check |
| not_null | mart_team_summary.team_name | Null check |
| not_null | mart_team_summary.match_id | Null check |

## Running the Project

```
# Install dependencies
conda activate soccer-pipeline
pip install dbt-core dbt-duckdb duckdb

# Download StatsBomb data
python data/download_data.py

# Run all models
dbt run

# Run all tests
dbt test

# Run models and tests together
dbt build
```

## Connection to Day 1 Pipeline

In production, the Parquet files read by this dbt project are produced by the AWS Lambda pipeline in 01_lambda_pipeline. The full platform flow is:

StatsBomb JSON -> S3 Raw Bucket -> Lambda -> Pandera Validation -> Parquet -> S3 Processed Bucket -> DuckDB -> dbt models -> Analytics

## Data Source

Uses StatsBomb Open Data (https://github.com/statsbomb/open-data) — freely available professional match data. StatsBomb is one of the leading soccer data providers used by professional clubs worldwide, and is explicitly listed as a data provider in Inter Miami CF's analytics infrastructure.

