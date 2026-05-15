with events as (
    select * from {{ ref('stg_events') }}
),

passes as (
    select
        match_id,
        team_name,
        player_name,
        count(*)                                                    as total_passes,
        count(case when pass_outcome is null then 1 end)            as completed_passes,
        count(case when pass_outcome = 'Incomplete' then 1 end)     as incomplete_passes,
        round(avg(pass_length), 2)                                  as avg_pass_length,
        count(case when pass_goal_assist = true then 1 end)         as goal_assists,
        count(case when pass_shot_assist = true then 1 end)         as shot_assists,
        count(case when pass_cross = true then 1 end)               as crosses,
        count(case when pass_through_ball = true then 1 end)        as through_balls,
        count(case when pass_switch = true then 1 end)              as switches
    from events
    where event_type = 'Pass'
    group by match_id, team_name, player_name
),

shots as (
    select
        match_id,
        team_name,
        player_name,
        count(*)                                                    as total_shots,
        count(case when shot_outcome = 'Goal' then 1 end)           as goals,
        count(case when shot_outcome = 'Saved' then 1 end)          as shots_saved,
        count(case when shot_outcome = 'On Target' then 1 end)      as shots_on_target,
        round(sum(shot_xg), 3)                                      as total_xg,
        round(avg(shot_xg), 3)                                      as avg_xg_per_shot,
        count(case when shot_first_time = true then 1 end)          as first_time_shots,
        count(case when shot_one_on_one = true then 1 end)          as one_on_ones,
        count(case when shot_open_goal = true then 1 end)           as open_goal_shots
    from events
    where event_type = 'Shot'
    group by match_id, team_name, player_name
),

dribbles as (
    select
        match_id,
        team_name,
        player_name,
        count(*)                                                    as total_dribbles,
        count(case when dribble_outcome = 'Complete' then 1 end)    as successful_dribbles
    from events
    where event_type = 'Dribble'
    group by match_id, team_name, player_name
),

all_players as (
    select distinct match_id, team_name, player_name
    from events
    where player_name is not null
)

select
    p.match_id,
    p.team_name,
    p.player_name,

    -- passing
    coalesce(pa.total_passes, 0)                                    as total_passes,
    coalesce(pa.completed_passes, 0)                                as completed_passes,
    coalesce(pa.incomplete_passes, 0)                               as incomplete_passes,
    case
        when coalesce(pa.total_passes, 0) > 0
        then round(coalesce(pa.completed_passes, 0) * 100.0 / pa.total_passes, 1)
        else 0
    end                                                             as pass_completion_pct,
    coalesce(pa.avg_pass_length, 0)                                 as avg_pass_length,
    coalesce(pa.goal_assists, 0)                                    as goal_assists,
    coalesce(pa.shot_assists, 0)                                    as shot_assists,
    coalesce(pa.crosses, 0)                                         as crosses,
    coalesce(pa.through_balls, 0)                                   as through_balls,

    -- shooting
    coalesce(s.total_shots, 0)                                      as total_shots,
    coalesce(s.goals, 0)                                            as goals,
    coalesce(s.shots_on_target, 0)                                  as shots_on_target,
    coalesce(s.total_xg, 0)                                         as total_xg,
    coalesce(s.avg_xg_per_shot, 0)                                  as avg_xg_per_shot,
    coalesce(s.first_time_shots, 0)                                 as first_time_shots,
    coalesce(s.one_on_ones, 0)                                      as one_on_ones,

    -- dribbling
    coalesce(d.total_dribbles, 0)                                   as total_dribbles,
    coalesce(d.successful_dribbles, 0)                              as successful_dribbles,
    case
        when coalesce(d.total_dribbles, 0) > 0
        then round(coalesce(d.successful_dribbles, 0) * 100.0 / d.total_dribbles, 1)
        else 0
    end                                                             as dribble_success_pct

from all_players p
left join passes pa
    on p.match_id = pa.match_id
    and p.player_name = pa.player_name
left join shots s
    on p.match_id = s.match_id
    and p.player_name = s.player_name
left join dribbles d
    on p.match_id = d.match_id
    and p.player_name = d.player_name