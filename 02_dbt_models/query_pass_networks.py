import duckdb

conn = duckdb.connect('dev.duckdb')

print('=== TOP PASS COMBINATIONS (ALL MATCHES) ===')
print(conn.execute('''
    select
        passer_name,
        recipient_name,
        team_name,
        sum(total_passes)                           as total_passes,
        round(avg(completion_pct), 1)               as avg_completion_pct,
        round(avg(avg_pass_length), 1)              as avg_length,
        sum(goal_assists)                           as goal_assists,
        sum(shot_assists)                           as shot_assists
    from mart_pass_networks
    group by passer_name, recipient_name, team_name
    order by total_passes desc
    limit 15
''').df().to_string(index=False))

print()
print('=== MOST CONNECTED PLAYERS (PASS NETWORK HUBS) ===')
print(conn.execute('''
    select
        passer_name,
        team_name,
        count(distinct recipient_name)              as unique_recipients,
        sum(total_passes)                           as total_passes_made,
        round(avg(completion_pct), 1)               as avg_completion_pct
    from mart_pass_networks
    group by passer_name, team_name
    order by unique_recipients desc
    limit 10
''').df().to_string(index=False))

print()
print('=== MOST DANGEROUS CONNECTIONS (SHOT + GOAL ASSISTS) ===')
print(conn.execute('''
    select
        passer_name,
        recipient_name,
        team_name,
        sum(total_passes)                           as total_passes,
        sum(goal_assists)                           as goal_assists,
        sum(shot_assists)                           as shot_assists,
        sum(goal_assists) + sum(shot_assists)       as total_chances_created
    from mart_pass_networks
    where goal_assists > 0 or shot_assists > 0
    group by passer_name, recipient_name, team_name
    order by total_chances_created desc
    limit 10
''').df().to_string(index=False))