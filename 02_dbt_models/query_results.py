import duckdb

conn = duckdb.connect('dev.duckdb')

print('=== TOP 10 PLAYERS BY PASSES (ALL MATCHES) ===')
print(conn.execute('''
    select player_name, team_name,
           sum(total_passes) as passes,
           round(avg(pass_completion_pct),1) as avg_completion_pct,
           sum(goals) as goals,
           round(sum(total_xg),2) as total_xg
    from mart_player_performance
    group by player_name, team_name
    order by passes desc
    limit 10
''').df().to_string(index=False))

print()
print('=== TEAM SUMMARY ===')
print(conn.execute('''
    select team_name,
           sum(total_passes) as passes,
           round(avg(pass_completion_pct),1) as avg_completion_pct,
           sum(total_shots) as shots,
           sum(goals) as goals,
           round(sum(total_xg),2) as total_xg
    from mart_team_summary
    group by team_name
    order by goals desc
    limit 10
''').df().to_string(index=False))

print()
print('=== SHOT ANALYSIS BY TIME BRACKET ===')
print(conn.execute('''
    select time_bracket,
           count(*) as shots,
           sum(case when is_goal then 1 else 0 end) as goals,
           round(avg(shot_xg),3) as avg_xg
    from mart_shot_analysis
    group by time_bracket
    order by time_bracket
''').df().to_string(index=False))