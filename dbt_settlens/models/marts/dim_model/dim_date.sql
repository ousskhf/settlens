{{ config(materialized='table') }}

SELECT
  Date,
  EXTRACT(YEAR FROM Date) AS Year,
  EXTRACT(WEEK FROM Date) AS Week,
  EXTRACT(DAY FROM Date) AS Day,
  FORMAT_DATE('%Q', Date) as Quarter,
  EXTRACT(MONTH FROM Date) AS Month,
  FORMAT_DATE('%B', Date) as Month_Name,
  CAST(FORMAT_DATE('%u', Date) AS INT64) AS Day_Of_Week,
  FORMAT_DATE('%A', Date) AS Day_Of_Week_Name,
  IF(FORMAT_DATE('%A', Date) IN ('Saturday', 'Sunday'), FALSE, TRUE) AS Is_Weekday,
  COUNT(Date) OVER (PARTITION BY EXTRACT(YEAR FROM Date), EXTRACT(MONTH FROM Date)) AS Days_In_Month

FROM
  UNNEST(
  -- set needed time range here
  GENERATE_DATE_ARRAY('2025-01-01', '2030-12-31', INTERVAL 1 DAY)
  ) AS Date
