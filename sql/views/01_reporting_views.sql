-- Reporting views for the Ascent Analytics warehouse.
-- Run after the schema and warehouse load (sql/schema/*.sql + build_warehouse.py).
--
-- These aren't required for Power BI (which can query the star schema
-- directly), but they demonstrate the SQL-side reporting layer and give
-- a single, tested source of truth for anything reused across dashboards
-- or ad hoc analysis. vw_bookings_enriched in particular is the base most
-- other views and queries build on.

DROP VIEW IF EXISTS vw_bookings_enriched;
CREATE VIEW vw_bookings_enriched AS
SELECT
    fb.booking_id,
    fb.booking_reference,
    fb.status,
    fb.party_size,
    fb.total_price,
    fb.lead_time_days,
    fb.season,
    d.full_date        AS tour_date,
    d.year              AS tour_year,
    d.month              AS tour_month,
    d.month_name          AS tour_month_name,
    d.quarter              AS tour_quarter,
    d.is_weekend             AS tour_is_weekend,
    cd.full_date               AS created_date,
    c.customer_id,
    c.contact_name,
    c.contact_email,
    rt.route_id,
    rt.name                      AS route_name,
    rt.difficulty,
    rt.distance_km,
    reg.region_id,
    reg.name                       AS region_name,
    g.guide_id,
    g.full_name                      AS guide_name,
    mc.channel_name                    AS marketing_channel
FROM FactBookings fb
JOIN DimDate d          ON fb.tour_date_id = d.date_id
JOIN DimDate cd         ON fb.created_date_id = cd.date_id
JOIN DimCustomer c      ON fb.customer_id = c.customer_id
JOIN DimRoute rt        ON fb.route_id = rt.route_id
JOIN DimRegion reg      ON fb.region_id = reg.region_id
LEFT JOIN DimGuide g    ON fb.guide_id = g.guide_id
LEFT JOIN DimMarketingChannel mc ON fb.channel_id = mc.channel_id;


DROP VIEW IF EXISTS vw_monthly_revenue;
CREATE VIEW vw_monthly_revenue AS
SELECT
    tour_year,
    tour_month,
    tour_month_name,
    COUNT(*)                                           AS bookings,
    SUM(CASE WHEN status = 'confirmed' THEN total_price ELSE 0 END) AS revenue,
    SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END)           AS cancellations,
    ROUND(
        1.0 * SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) / COUNT(*), 4
    ) AS cancellation_rate
FROM vw_bookings_enriched
GROUP BY tour_year, tour_month, tour_month_name;


DROP VIEW IF EXISTS vw_route_performance;
CREATE VIEW vw_route_performance AS
SELECT
    b.route_id,
    b.route_name,
    b.region_name,
    b.difficulty,
    COUNT(*)                                                         AS bookings,
    SUM(CASE WHEN b.status = 'confirmed' THEN b.total_price ELSE 0 END) AS revenue,
    ROUND(1.0 * SUM(CASE WHEN b.status = 'cancelled' THEN 1 ELSE 0 END) / COUNT(*), 4) AS cancellation_rate,
    ROUND(AVG(fr.overall_rating), 2)                                    AS avg_overall_rating
FROM vw_bookings_enriched b
LEFT JOIN FactReviews fr ON b.booking_id = fr.booking_id
GROUP BY b.route_id, b.route_name, b.region_name, b.difficulty;


DROP VIEW IF EXISTS vw_guide_performance;
CREATE VIEW vw_guide_performance AS
SELECT
    g.guide_id,
    g.full_name,
    g.employment_type,
    g.day_rate_gbp,
    COUNT(fb.booking_id)                                                  AS bookings,
    SUM(CASE WHEN fb.status = 'confirmed' THEN fb.total_price ELSE 0 END)  AS revenue,
    ROUND(1.0 * SUM(CASE WHEN fb.status = 'cancelled' THEN 1 ELSE 0 END) / NULLIF(COUNT(fb.booking_id), 0), 4) AS cancellation_rate,
    ROUND(AVG(fr.guide_rating), 2)                                        AS avg_guide_rating,
    ROUND(AVG(fr.safety_rating), 2)                                       AS avg_safety_rating
FROM DimGuide g
LEFT JOIN FactBookings fb ON g.guide_id = fb.guide_id
LEFT JOIN FactReviews fr  ON fb.booking_id = fr.booking_id
GROUP BY g.guide_id, g.full_name, g.employment_type, g.day_rate_gbp;


DROP VIEW IF EXISTS vw_customer_summary;
CREATE VIEW vw_customer_summary AS
SELECT
    c.customer_id,
    c.contact_name,
    c.contact_email,
    COUNT(fb.booking_id)                                                 AS total_bookings,
    SUM(CASE WHEN fb.status = 'confirmed' THEN fb.total_price ELSE 0 END) AS lifetime_value,
    MIN(d.full_date)                                                     AS first_booking_date,
    MAX(d.full_date)                                                     AS last_booking_date,
    CASE WHEN COUNT(fb.booking_id) > 1 THEN 1 ELSE 0 END                 AS is_repeat_customer
FROM DimCustomer c
JOIN FactBookings fb ON c.customer_id = fb.customer_id
JOIN DimDate d ON fb.tour_date_id = d.date_id
GROUP BY c.customer_id, c.contact_name, c.contact_email;


-- Weather-related cancellations: joins cancelled bookings to same-date,
-- same-region weather, flagging cancellations that coincide with a storm
-- warning or heavy rain. See docs/data_dictionary/README.md — this is an
-- analytical join, not a claim that weather directly caused each
-- cancellation in the source system.
DROP VIEW IF EXISTS vw_weather_flagged_cancellations;
CREATE VIEW vw_weather_flagged_cancellations AS
SELECT
    b.booking_id,
    b.route_name,
    b.region_name,
    b.tour_date,
    w.storm_warning,
    w.rain_mm,
    CASE WHEN w.storm_warning = 1 OR w.rain_mm > 15 THEN 1 ELSE 0 END AS weather_flagged
FROM vw_bookings_enriched b
JOIN FactWeather w ON b.region_id = w.region_id
JOIN DimDate wd ON w.date_id = wd.date_id AND wd.full_date = b.tour_date
WHERE b.status = 'cancelled';


DROP VIEW IF EXISTS vw_marketing_performance;
CREATE VIEW vw_marketing_performance AS
SELECT
    mc.channel_name,
    mc.channel_type,
    d.year,
    d.month,
    SUM(fm.spend)         AS spend,
    SUM(fm.clicks)         AS clicks,
    SUM(fm.impressions)     AS impressions,
    SUM(fm.conversions)      AS conversions,
    SUM(fm.revenue)           AS revenue,
    CASE WHEN SUM(fm.spend) > 0 THEN ROUND(SUM(fm.revenue) / SUM(fm.spend), 2) ELSE NULL END AS roas,
    CASE WHEN SUM(fm.conversions) > 0 THEN ROUND(SUM(fm.spend) / SUM(fm.conversions), 2) ELSE 0 END AS cost_per_booking
FROM FactMarketing fm
JOIN DimMarketingChannel mc ON fm.channel_id = mc.channel_id
JOIN DimDate d ON fm.month_date_id = d.date_id
GROUP BY mc.channel_name, mc.channel_type, d.year, d.month;