with events as (
    select * from {{ ref('stg_events') }}
),

shots as (
    select
        event_id,
        match_id,
        home_team,
        away_team,
        team_name,
        player_name,
        minute,
        second,
        period,
        shot_outcome,
        shot_body_part,
        shot_technique,
        shot_type,
        shot_xg,
        shot_first_time,
        shot_one_on_one,
        shot_open_goal,
        location,
        play_pattern,
        under_pressure
    from events
    where event_type = 'Shot'
),

enriched as (
    select
        event_id,
        match_id,
        home_team,
        away_team,
        team_name,
        player_name,
        period,
        minute,
        second,
        play_pattern,

        -- shot details
        shot_outcome,
        shot_body_part,
        shot_technique,
        shot_type,
        coalesce(shot_xg, 0)                                    as shot_xg,

        -- shot flags
        coalesce(shot_first_time, false)                        as is_first_time,
        coalesce(shot_one_on_one, false)                        as is_one_on_one,
        coalesce(shot_open_goal, false)                         as is_open_goal,
        coalesce(under_pressure, false)                         as is_under_pressure,

        -- outcome flags
        case when shot_outcome = 'Goal' then true
             else false end                                     as is_goal,
        case when shot_outcome in ('Goal', 'Saved')
             then true else false end                           as is_on_target,

        -- match context
        case
            when minute < 15 then '0-15'
            when minute < 30 then '15-30'
            when minute < 45 then '30-45'
            when minute < 60 then '45-60'
            when minute < 75 then '60-75'
            else '75+'
        end                                                     as time_bracket,

        -- location
        location

    from shots
)

select * from enriched