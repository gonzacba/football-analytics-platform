with events as (
    select * from {{ ref('stg_events') }}
),

team_passes as (
    select
        match_id,
        team_name,
        home_team,
        away_team,
        count(*)                                                as total_passes,
        count(case when pass_outcome is null then 1 end)        as completed_passes,
        count(case when pass_cross = true then 1 end)           as crosses,
        count(case when pass_through_ball = true then 1 end)    as through_balls,
        count(case when pass_switch = true then 1 end)          as switches,
        count(case when pass_goal_assist = true then 1 end)     as assists,
        round(avg(pass_length), 2)                              as avg_pass_length
    from events
    where event_type = 'Pass'
    group by match_id, team_name, home_team, away_team
),

team_shots as (
    select
        match_id,
        team_name,
        count(*)                                                as total_shots,
        count(case when shot_outcome = 'Goal' then 1 end)       as goals,
        count(case when shot_outcome = 'Saved' then 1 end)      as shots_saved,
        round(sum(shot_xg), 3)                                  as total_xg,
        count(case when shot_open_goal = true then 1 end)       as open_goal_shots,
        count(case when shot_one_on_one = true then 1 end)      as one_on_ones
    from events
    where event_type = 'Shot'
    group by match_id, team_name
),

team_dribbles as (
    select
        match_id,
        team_name,
        count(*)                                                        as total_dribbles,
        count(case when dribble_outcome = 'Complete' then 1 end)        as successful_dribbles
    from events
    where event_type = 'Dribble'
    group by match_id, team_name
),

team_pressure as (
    select
        match_id,
        team_name,
        count(*)                                                as total_pressures
    from events
    where event_type = 'Pressure'
    group by match_id, team_name
)

select
    p.match_id,
    p.team_name,
    p.home_team,
    p.away_team,
    case
        when p.team_name = p.home_team then 'Home'
        else 'Away'
    end                                                         as home_away,

    -- passing
    coalesce(p.total_passes, 0)                                 as total_passes,
    coalesce(p.completed_passes, 0)                             as completed_passes,
    case
        when coalesce(p.total_passes, 0) > 0
        then round(p.completed_passes * 100.0 / p.total_passes, 1)
        else 0
    end                                                         as pass_completion_pct,
    coalesce(p.avg_pass_length, 0)                              as avg_pass_length,
    coalesce(p.crosses, 0)                                      as crosses,
    coalesce(p.through_balls, 0)                                as through_balls,
    coalesce(p.assists, 0)                                      as assists,

    -- shooting
    coalesce(s.total_shots, 0)                                  as total_shots,
    coalesce(s.goals, 0)                                        as goals,
    coalesce(s.shots_saved, 0)                                  as shots_saved,
    coalesce(s.total_xg, 0)                                     as total_xg,
    coalesce(s.one_on_ones, 0)                                  as one_on_ones,

    -- dribbling
    coalesce(d.total_dribbles, 0)                               as total_dribbles,
    coalesce(d.successful_dribbles, 0)                          as successful_dribbles,

    -- pressing
    coalesce(pr.total_pressures, 0)                             as total_pressures

from team_passes p
left join team_shots s
    on p.match_id = s.match_id
    and p.team_name = s.team_name
left join team_dribbles d
    on p.match_id = d.match_id
    and p.team_name = d.team_name
left join team_pressure pr
    on p.match_id = pr.match_id
    and p.team_name = pr.team_name