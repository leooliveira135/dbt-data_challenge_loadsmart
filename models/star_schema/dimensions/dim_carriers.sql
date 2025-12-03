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
with dim_carriers as (

    select
        loadsmart_id,
        carrier_rating,
        vip_carrier,
        carrier_dropped_us_count,
        carrier_name,
        carrier_on_time_to_pickup,
        carrier_on_time_to_delivery,
        carrier_on_time_overall
    from {{ source('loadsmart', 'data_challenge') }}

)

select * from dim_carriers;
