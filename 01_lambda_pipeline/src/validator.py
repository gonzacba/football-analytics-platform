import pandera.pandas as pa
from pandera.pandas import Column, DataFrameSchema

events_schema = DataFrameSchema({
    "id": Column(str, nullable=False),
    "index": Column(int, nullable=False),
    "period": Column(int, pa.Check.isin([1, 2, 3, 4, 5])),
    "timestamp": Column(str, nullable=False),
    "type": Column(str, nullable=False),
    "team": Column(str, nullable=False),
    "player": Column(str, nullable=True),
})

def validate_events(df):
    """Validate raw StatsBomb event data against schema."""
    return events_schema.validate(df, lazy=True)