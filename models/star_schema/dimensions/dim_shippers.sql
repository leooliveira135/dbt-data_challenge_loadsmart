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
with dim_shippers as (

    select
        loadsmart_id,
        pnl,
        mileage,
        equipment_type,
        sourcing_channel,
        shipper_name
    from {{ source('loadsmart', 'data_challenge') }}

)

select * from dim_shippers;
