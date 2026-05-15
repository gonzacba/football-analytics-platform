import pandas as pd
import json
import io
import pyarrow as pa
import pyarrow.parquet as pq

def load_events_from_json(events: list) -> pd.DataFrame:
    """Flatten raw StatsBomb JSON events into a DataFrame."""
    df = pd.json_normalize(events)

    # Standardize column names
    df.columns = [col.replace(".", "_").lower() for col in df.columns]

    # Map to clean column names
    rename_map = {
        "type_name": "type",
        "team_name": "team",
        "player_name": "player"
    }
    df = df.rename(columns=rename_map)

    # Keep only core columns that exist
    core_cols = [c for c in ["id", "index", "period", "timestamp", "type", "team", "player", "location"] if c in df.columns]
    df = df[core_cols].copy()

    # Ensure correct types
    df["id"] = df["id"].astype(str)
    df["index"] = df["index"].astype(int)
    df["period"] = df["period"].astype(int)
    df["timestamp"] = df["timestamp"].astype(str)
    df["type"] = df["type"].astype(str)
    df["team"] = df["team"].astype(str)

    return df

def to_parquet_bytes(df: pd.DataFrame) -> bytes:
    """Serialize DataFrame to Parquet bytes for S3 upload."""
    buffer = io.BytesIO()
    table = pa.Table.from_pandas(df)
    pq.write_table(table, buffer)
    return buffer.getvalue()