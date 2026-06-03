import json
import os
from statsbombpy import sb
import pandas as pd

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

print("Fetching FIFA World Cup 2022 data...")

# FIFA World Cup 2022 — competition_id=43, season_id=106
matches = sb.matches(competition_id=43, season_id=106)
print(f"Found {len(matches)} matches")

# Download all 64 matches
all_events = []
for i, row in matches.iterrows():
    match_id = row["match_id"]
    home = row["home_team"]
    away = row["away_team"]
    home_score = row["home_score"]
    away_score = row["away_score"]
    print(f"Downloading match {match_id}: {home} {home_score}-{away_score} {away}")
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
print(f"Columns: {len(df.columns)} columns")
print(f"Matches: {df['match_id'].nunique()} matches")
print(f"Teams: {df['team'].nunique()} teams")