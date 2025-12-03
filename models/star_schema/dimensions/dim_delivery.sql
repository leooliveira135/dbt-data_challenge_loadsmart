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
with dim_delivery as (

    select
        loadsmart_id,
        split(split(lane, ' -> ')[2], ',')[1] as delivery_city,
        split(split(lane, ' -> ')[2], ',')[2] as delivery_state,
        delivery_date,
        delivery_appointment_time
    from {{ source('loadsmart', 'data_challenge') }}

)

select * from dim_delivery;
