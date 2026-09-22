{{ config(materialized='table') }}

SELECT
    calendar_date,
    CAST(FORMAT_DATE('%u', calendar_date) AS INT64) AS day_of_week,
    EXTRACT(YEAR FROM calendar_date) AS year,
    EXTRACT(WEEK FROM calendar_date) AS week_number,
    EXTRACT(DAY FROM calendar_date) AS day,
    FORMAT_DATE('%Q', calendar_date) AS quarter_number,
    EXTRACT(MONTH FROM calendar_date) AS month,
    FORMAT_DATE('%B', calendar_date) AS month_name,
    FORMAT_DATE('%A', calendar_date) AS day_of_week_name,
    IF(FORMAT_DATE('%A', calendar_date) IN ('Saturday', 'Sunday'), FALSE, TRUE)
        AS is_weekday,
    COUNT(calendar_date)
        OVER (
            PARTITION BY
                EXTRACT(YEAR FROM calendar_date),
                EXTRACT(MONTH FROM calendar_date)
        )
        AS days_in_month

FROM
    UNNEST(
        -- set needed time range here
        GENERATE_DATE_ARRAY('2025-01-01', '2030-12-31', INTERVAL 1 DAY)
    ) AS calendar_date
