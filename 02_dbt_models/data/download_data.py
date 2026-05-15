import json
import os
from statsbombpy import sb
import pandas as pd

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

print("Fetching StatsBomb free data...")

# Get La Liga 2005/06 matches (competition_id=11, season_id=1)
matches = sb.matches(competition_id=11, season_id=1)
print(f"Found {len(matches)} matches")

# Download first 10 matches
all_events = []
for i, row in matches.head(10).iterrows():
    match_id = row["match_id"]
    home = row["home_team"]
    away = row["away_team"]
    print(f"Downloading match {match_id}: {home} vs {away}")
    events = sb.events(match_id=match_id)
    events["match_id"] = match_id
    events["home_team"] = home
    events["away_team"] = away
    all_events.append(events)

# Combine all matches
df = pd.concat(all_events, ignore_index=True)
print(f"\nTotal events: {len(df)}")

# Save as parquet
output_path = os.path.join(OUTPUT_DIR, "events.parquet")
df.to_parquet(output_path, index=False)
print(f"Saved to {output_path}")
print(f"Columns: {list(df.columns)}")