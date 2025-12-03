{{ config(
    materialized = "table",
    schema = "analytics",
    tags = ["transform"]
) }}

-- ============================================================================
-- Model: your_model
-- Description: Brief description of what this model does.
-- Author: Leonardo Oliveira
-- ============================================================================

-- Documentation block (optional in .yml instead)

-- ============================================================================
-- CTE Section
-- ============================================================================

-- 1. Source data
with dim_pickup as (

    select
        loadsmart_id,
        split(split(lane, ' -> ')[1], ',')[1] as pickup_city,
        split(split(lane, ' -> ')[1], ',')[2] as pickup_state,
        pickup_date,
        pickup_appointment_time
    from {{ source('loadsmart', 'data_challenge') }}

)

select * from dim_pickup;
