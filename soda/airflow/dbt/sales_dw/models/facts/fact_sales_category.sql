{{
    config(
        materialized='table'
    )
}}

SELECT
    u.user_id,
    p.category,
    SUM(
        CAST(
            NULLIF(REGEXP_REPLACE(actual_price, '[^0-9.]', ''), '') AS DECIMAL(10,2)
        )
    ) AS sales_amount
FROM
    {{ ref('stg_sales_eph') }} s
    JOIN {{ ref('dim_product') }} p ON s.product_id = p.product_id
    JOIN {{ ref('dim_user') }} u ON s.user_id = u.user_id
GROUP BY
    u.user_id,
    p.category