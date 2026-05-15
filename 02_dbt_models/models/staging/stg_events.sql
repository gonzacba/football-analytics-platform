with source as (
    select * from {{ ref('base_events') }}
),

renamed as (
    select
        -- identifiers
        id                                          as event_id,
        match_id,
        index                                       as event_index,

        -- match context
        period,
        minute,
        second,
        timestamp                                   as event_timestamp,
        home_team,
        away_team,

        -- event details
        type                                        as event_type,
        team                                        as team_name,
        player                                      as player_name,
        player_id,
        position                                    as player_position,
        play_pattern,
        under_pressure,

        -- pass details
        pass_length,
        pass_angle,
        pass_height,
        pass_body_part,
        pass_outcome,
        pass_type,
        pass_cross,
        pass_switch,
        pass_through_ball,
        pass_goal_assist,
        pass_shot_assist,
        pass_recipient                              as pass_recipient_name,

        -- shot details
        shot_statsbomb_xg                           as shot_xg,
        shot_outcome,
        shot_body_part,
        shot_technique,
        shot_type,
        shot_first_time,
        shot_one_on_one,
        shot_open_goal,

        -- carry details
        carry_end_location,

        -- dribble details
        dribble_outcome,

        -- location
        location

    from source
)

select * from renamed