{{
    config(
        materialized='table'
    )
}}

SELECT
    user_id,
    product_id,
    TRY_CAST(REPLACE(rating, ',', '.') AS DECIMAL(3,2)) AS rating,
    TRY_CAST(REPLACE(rating_count, ',', '.') AS BIGINT) AS rating_count
FROM {{ ref('stg_sales_eph') }}
