-- Cohort retention: for customers acquired in a given signup month
-- (first booking = signup, since there's no separate signup event),
-- what % had booked again by 6 and 12 months later.
-- Demonstrates: CTEs (multiple, chained), window functions (MIN OVER),
-- conditional aggregation.
--
-- Business question: "Which customers return, and how strong is
-- retention by cohort?" (docs/business_problem.md, Q4)

WITH first_booking AS (
    SELECT
        fb.customer_id,
        MIN(d.full_date) AS first_booking_date
    FROM FactBookings fb
    JOIN DimDate d ON fb.tour_date_id = d.date_id
    WHERE fb.status IN ('confirmed', 'amended')
    GROUP BY fb.customer_id
),
cohorts AS (
    SELECT
        customer_id,
        first_booking_date,
        strftime('%Y-%m', first_booking_date) AS cohort_month
    FROM first_booking
),
customer_bookings AS (
    SELECT fb.customer_id, d.full_date AS tour_date
    FROM FactBookings fb
    JOIN DimDate d ON fb.tour_date_id = d.date_id
    WHERE fb.status IN ('confirmed', 'amended')
),
rebookings AS (
    SELECT
        c.customer_id,
        c.cohort_month,
        MAX(CASE WHEN JULIANDAY(cb.tour_date) - JULIANDAY(c.first_booking_date) BETWEEN 1 AND 182 THEN 1 ELSE 0 END) AS rebooked_within_6m,
        MAX(CASE WHEN JULIANDAY(cb.tour_date) - JULIANDAY(c.first_booking_date) BETWEEN 1 AND 365 THEN 1 ELSE 0 END) AS rebooked_within_12m
    FROM cohorts c
    LEFT JOIN customer_bookings cb ON c.customer_id = cb.customer_id
    GROUP BY c.customer_id, c.cohort_month
)
SELECT
    cohort_month,
    COUNT(*) AS cohort_size,
    SUM(rebooked_within_6m)  AS rebooked_6m,
    SUM(rebooked_within_12m) AS rebooked_12m,
    ROUND(1.0 * SUM(rebooked_within_6m) / COUNT(*), 4)  AS retention_6m,
    ROUND(1.0 * SUM(rebooked_within_12m) / COUNT(*), 4) AS retention_12m
FROM rebookings
GROUP BY cohort_month
-- exclude the most recent cohorts, which haven't had 12 months to rebook yet
HAVING cohort_month <= strftime('%Y-%m', (SELECT MAX(full_date) FROM DimDate), '-13 months')
ORDER BY cohort_month;