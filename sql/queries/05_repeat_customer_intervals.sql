-- Repeat customers and rebooking interval.
-- Demonstrates: CTEs, window functions (LEAD), self-referencing analysis
-- without a self-join.
--
-- Business question: "Which customers return, and how long is the typical
-- gap between bookings?" (docs/business_problem.md, Q4)

WITH customer_bookings AS (
    SELECT
        fb.customer_id,
        c.contact_name,
        d.full_date AS tour_date,
        ROW_NUMBER() OVER (PARTITION BY fb.customer_id ORDER BY d.full_date) AS booking_sequence
    FROM FactBookings fb
    JOIN DimCustomer c ON fb.customer_id = c.customer_id
    JOIN DimDate d ON fb.tour_date_id = d.date_id
    WHERE fb.status IN ('confirmed', 'amended')
),
with_next_booking AS (
    SELECT
        customer_id,
        contact_name,
        tour_date,
        booking_sequence,
        LEAD(tour_date) OVER (PARTITION BY customer_id ORDER BY tour_date) AS next_booking_date
    FROM customer_bookings
)
SELECT
    customer_id,
    contact_name,
    tour_date AS booking_date,
    next_booking_date,
    CAST(JULIANDAY(next_booking_date) - JULIANDAY(tour_date) AS INTEGER) AS days_to_next_booking
FROM with_next_booking
WHERE next_booking_date IS NOT NULL
ORDER BY days_to_next_booking
LIMIT 50;