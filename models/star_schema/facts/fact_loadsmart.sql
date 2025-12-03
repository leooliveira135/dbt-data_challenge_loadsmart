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

with dim_book as (
    select 
        loadsmart_id,
        quote_date,
        book_date,
        source_date,
        book_price,
        source_price
    from {{ ref('dim_book') }}
),

dim_carriers as (
    select 
        loadsmart_id,
        carrier_rating,
        carrier_dropped_us_count
    from {{ ref('dim_carriers') }}
),

dim_delivery as (
    select 
        loadsmart_id,
        delivery_date,
        delivery_appointment_time
    from {{ ref('dim_delivery') }}
),

dim_pickup as (
    select 
        loadsmart_id,
        pickup_date,
        pickup_appointment_time
    from {{ ref('dim_pickup') }}
),

dim_shippers as (
    select 
        loadsmart_id,
        pnl,
        mileage
    from {{ ref('dim_shippers') }}
),

fact as (
    select
        source.loadsmart_id,
        book.quote_date,
        book.book_date,
        book.source_date,
        book.book_price,
        book.source_price,
        carriers.carrier_rating,
        carriers.carrier_dropped_us_count,
        delivery.delivery_date,
        delivery.delivery_appointment_time,
        pickup.pickup_date,
        pickup.pickup_appointment_time,
        shippers.pnl,
        shippers.mileage
    from {{ source("loadsmart", "data_challenge") }} as source
    left join dim_book as book
    on source.loadsmart_id = book.loadsmart_id
    left join dim_carriers as carriers
    on source.loadsmart_id = carriers.loadsmart_id
    left join dim_delivery as delivery
    on source.loadsmart_id = delivery.loadsmart_id
    left join dim_pickup as pickup
    on source.loadsmart_id = pickup.loadsmart_id
    left join dim_shippers as shippers
    on source.loadsmart_id = shippers.loadsmart_id
)

select * from fact;
