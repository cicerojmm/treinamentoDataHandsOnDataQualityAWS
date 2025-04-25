{% test test_assert_valid_rating(model, column_name) %}

SELECT *
FROM {{ model }}
WHERE {{ column_name }} IS NULL

{% endtest %}