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
with dim_book as (

    select
        loadsmart_id,
        quote_date,
        book_date,
        source_date,
        book_price,
        source_price,
        has_mobile_app_tracking23,
        has_mobile_app_tracking24,
        has_macropoint_tracking,
        has_edi_tracking,
        contracted_load,
        load_booked_autonomously,
        load_sourced_autonomously,
        load_was_cancelled
    from {{ source('loadsmart', 'data_challenge') }}

)

select * from dim_book;
