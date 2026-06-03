from statsbombpy import sb

comps = sb.competitions()
wc = comps[comps['competition_name'] == 'FIFA World Cup']
print(wc[['competition_id', 'season_id', 'season_name']])