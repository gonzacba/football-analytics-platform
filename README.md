# Soccer Analytics Platform

A production-grade soccer analytics platform built on AWS and dbt, 
using StatsBomb open data to mirror the data infrastructure used by 
professional soccer clubs.

## Projects

### 01 — AWS Lambda Pipeline
Event-driven data pipeline using Lambda and S3 to ingest StatsBomb 
match event data, with Pandera schema validation and JSON-to-Parquet 
transformation via PyArrow.

### 02 — dbt Transformation Layer
3-layer dbt architecture (base → staging → mart) on 38,000+ match 
events producing player performance, team summary, and shot analytics.

## Tech Stack
AWS Lambda, S3, IAM, CloudWatch, Python, Pandas, PyArrow, Pandera, 
dbt Core, DuckDB, pytest, moto, GitHub Actions, StatsBomb Open Data

## CI/CD
![Tests](https://github.com/gonzacba/soccer-analytics-platform/actions/workflows/test.yml/badge.svg)