-- Cancellation drivers: buckets cancelled bookings by likely cause using
-- CASE logic, cross-referencing the weather-flagged-cancellations view.
-- Demonstrates: CASE, LEFT JOIN, subqueries, GROUP BY.
--
-- Business question: "What causes cancellations, and which weather
-- conditions matter?" (docs/business_problem.md, Q5/Q6)

SELECT
    reg.name AS region,
    d.month_name,
    COUNT(*) AS total_cancellations,
    SUM(CASE WHEN wfc.weather_flagged = 1 THEN 1 ELSE 0 END) AS weather_flagged_cancellations,
    ROUND(
        1.0 * SUM(CASE WHEN wfc.weather_flagged = 1 THEN 1 ELSE 0 END) / COUNT(*), 4
    ) AS weather_flagged_share,
    CASE
        WHEN d.month IN (11, 12, 1, 2, 3) THEN 'Winter season'
        ELSE 'Summer season'
    END AS season_bucket
FROM FactBookings fb
JOIN DimRegion reg ON fb.region_id = reg.region_id
JOIN DimDate d ON fb.tour_date_id = d.date_id
LEFT JOIN vw_weather_flagged_cancellations wfc ON fb.booking_id = wfc.booking_id
WHERE fb.status = 'cancelled'
GROUP BY reg.name, d.month_name, season_bucket
ORDER BY total_cancellations DESC;