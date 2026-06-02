with events as (
    select * from {{ ref('stg_events') }}
),

passes as (
    select
        match_id,
        home_team,
        away_team,
        team_name,
        player_name                                         as passer_name,
        pass_recipient_name                                 as recipient_name,
        pass_length,
        pass_angle,
        pass_height,
        pass_body_part,
        pass_outcome,
        pass_cross,
        pass_through_ball,
        pass_switch,
        pass_goal_assist,
        pass_shot_assist,
        period,
        minute
    from events
    where
        event_type = 'Pass'
        and player_name is not null
        and pass_recipient_name is not null
),

network as (
    select
        match_id,
        home_team,
        away_team,
        team_name,
        passer_name,
        recipient_name,

        -- volume
        count(*)                                            as total_passes,
        count(case when pass_outcome is null then 1 end)    as completed_passes,
        count(case when pass_outcome = 'Incomplete'
                   then 1 end)                              as incomplete_passes,

        -- distance
        round(avg(pass_length), 2)                          as avg_pass_length,
        round(min(pass_length), 2)                          as min_pass_length,
        round(max(pass_length), 2)                          as max_pass_length,

        -- pass types on this connection
        count(case when pass_cross = true then 1 end)       as crosses,
        count(case when pass_through_ball = true
                   then 1 end)                              as through_balls,
        count(case when pass_switch = true then 1 end)      as switches,
        count(case when pass_goal_assist = true
                   then 1 end)                              as goal_assists,
        count(case when pass_shot_assist = true
                   then 1 end)                              as shot_assists,

        -- timing
        round(avg(minute), 1)                               as avg_minute,

        -- completion rate
        case
            when count(*) > 0
            then round(
                count(case when pass_outcome is null then 1 end)
                * 100.0 / count(*), 1)
            else 0
        end                                                 as completion_pct

    from passes
    group by
        match_id,
        home_team,
        away_team,
        team_name,
        passer_name,
        recipient_name
)

select
    match_id,
    home_team,
    away_team,
    team_name,
    passer_name,
    recipient_name,
    total_passes,
    completed_passes,
    incomplete_passes,
    completion_pct,
    avg_pass_length,
    min_pass_length,
    max_pass_length,
    crosses,
    through_balls,
    switches,
    goal_assists,
    shot_assists,
    avg_minute
from network
where total_passes >= 2
order by match_id, team_name, total_passes desc