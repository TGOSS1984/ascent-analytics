-- Executive revenue KPIs by region.
-- Demonstrates: INNER JOIN, GROUP BY, HAVING, CASE, aggregate functions.
--
-- Business question: "Which regions are most profitable, and which have a
-- cancellation rate worth investigating?" (see docs/business_problem.md, Q1/Q8)

SELECT
    reg.name                                                              AS region,
    COUNT(*)                                                              AS total_bookings,
    SUM(CASE WHEN fb.status = 'confirmed' THEN fb.total_price ELSE 0 END) AS revenue,
    ROUND(AVG(CASE WHEN fb.status = 'confirmed' THEN fb.total_price END), 2) AS avg_booking_value,
    SUM(CASE WHEN fb.status = 'cancelled' THEN 1 ELSE 0 END)              AS cancellations,
    ROUND(1.0 * SUM(CASE WHEN fb.status = 'cancelled' THEN 1 ELSE 0 END) / COUNT(*), 4) AS cancellation_rate
FROM FactBookings fb
INNER JOIN DimRegion reg ON fb.region_id = reg.region_id
GROUP BY reg.name
-- only surface regions with enough volume for the cancellation rate to be meaningful
HAVING COUNT(*) >= 100
ORDER BY revenue DESC;