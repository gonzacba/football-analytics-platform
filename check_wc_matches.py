from statsbombpy import sb

matches = sb.matches(competition_id=43, season_id=106)
print(f"Total matches: {len(matches)}")
print(matches[['match_id', 'home_team', 'away_team', 'home_score', 'away_score']].to_string())