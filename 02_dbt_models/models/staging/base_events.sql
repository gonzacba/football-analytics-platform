{{ config(materialized='table') }}

select * from read_parquet('data/events.parquet')