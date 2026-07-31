-- Top 3 highest-revenue routes within each region.
-- Demonstrates: window functions (RANK), CTEs, PARTITION BY.
--
-- Business question: "Which routes are most profitable within each
-- region?" (docs/business_problem.md, Q1)

WITH route_revenue AS (
    SELECT
        reg.name    AS region,
        rt.name     AS route,
        rt.difficulty,
        SUM(fb.total_price) AS revenue,
        COUNT(*)             AS bookings
    FROM FactBookings fb
    JOIN DimRoute rt   ON fb.route_id = rt.route_id
    JOIN DimRegion reg ON fb.region_id = reg.region_id
    WHERE fb.status = 'confirmed'
    GROUP BY reg.name, rt.name, rt.difficulty
),
ranked AS (
    SELECT
        region,
        route,
        difficulty,
        revenue,
        bookings,
        RANK() OVER (PARTITION BY region ORDER BY revenue DESC) AS revenue_rank
    FROM route_revenue
)
SELECT region, route, difficulty, revenue, bookings, revenue_rank
FROM ranked
WHERE revenue_rank <= 3
ORDER BY region, revenue_rank;