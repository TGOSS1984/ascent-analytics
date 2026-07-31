-- Guide leaderboard: ranks guides by a simple composite of revenue and
-- average rating, within their primary region.
-- Demonstrates: window functions (ROW_NUMBER), LEFT JOIN, NULLIF, CTEs.
--
-- Business question: "Which guides perform best?" (docs/business_problem.md, Q2)

WITH guide_stats AS (
    SELECT
        g.guide_id,
        g.full_name,
        reg.name AS primary_region,
        COUNT(fb.booking_id) AS bookings,
        SUM(CASE WHEN fb.status = 'confirmed' THEN fb.total_price ELSE 0 END) AS revenue,
        ROUND(AVG(fr.overall_rating), 2) AS avg_rating,
        ROUND(1.0 * SUM(CASE WHEN fb.status = 'cancelled' THEN 1 ELSE 0 END) / NULLIF(COUNT(fb.booking_id), 0), 4) AS cancellation_rate
    FROM DimGuide g
    JOIN DimRegion reg      ON g.primary_region_id = reg.region_id
    LEFT JOIN FactBookings fb ON g.guide_id = fb.guide_id
    LEFT JOIN FactReviews fr  ON fb.booking_id = fr.booking_id
    WHERE g.active = 1
    GROUP BY g.guide_id, g.full_name, reg.name
)
SELECT
    primary_region,
    full_name,
    bookings,
    revenue,
    avg_rating,
    cancellation_rate,
    ROW_NUMBER() OVER (PARTITION BY primary_region ORDER BY revenue DESC) AS region_revenue_rank
FROM guide_stats
ORDER BY primary_region, region_revenue_rank;