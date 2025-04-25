{% test test_column_values_between(model, column_name, min_value, max_value) %}

WITH validation AS (
    SELECT
        {{ column_name }} AS invalid_value,
        *
    FROM {{ model }}
    WHERE {{ column_name }} < {{ min_value }} OR {{ column_name }} > {{ max_value }}
)

SELECT *
FROM validation

{% endtest %}