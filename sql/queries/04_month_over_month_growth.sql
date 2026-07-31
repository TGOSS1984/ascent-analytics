-- Month-over-month revenue growth.
-- Demonstrates: window functions (LAG), CTEs, percentage-change calculation.
--
-- Business question: "How is the business growing over time, and where
-- are the shocks (e.g. the 2020 COVID dip)?" (docs/business_problem.md, Q8)

WITH monthly AS (
    SELECT
        d.year,
        d.month,
        d.month_name,
        SUM(CASE WHEN fb.status = 'confirmed' THEN fb.total_price ELSE 0 END) AS revenue
    FROM FactBookings fb
    JOIN DimDate d ON fb.tour_date_id = d.date_id
    GROUP BY d.year, d.month, d.month_name
)
SELECT
    year,
    month,
    month_name,
    revenue,
    LAG(revenue) OVER (ORDER BY year, month) AS prior_month_revenue,
    ROUND(
        100.0 * (revenue - LAG(revenue) OVER (ORDER BY year, month))
        / NULLIF(LAG(revenue) OVER (ORDER BY year, month), 0),
        1
    ) AS mom_growth_pct
FROM monthly
ORDER BY year, month;