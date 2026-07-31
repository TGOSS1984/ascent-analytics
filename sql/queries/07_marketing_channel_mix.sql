-- Every marketing channel's contribution, using RIGHT JOIN so the query
-- is structurally guaranteed to keep every channel even if a channel had
-- zero attributed conversions in a given month. In this particular
-- dataset every channel has at least one attributed booking every month
-- (there's enough volume that a fully quiet channel-month doesn't occur),
-- so the result here matches what an INNER JOIN would return — the point
-- is the query no longer depends on that being true.
-- Demonstrates: RIGHT JOIN, COALESCE.
--
-- Note: RIGHT JOIN requires SQLite 3.39+ (2022). If your SQLite build is
-- older, swap the two tables and use LEFT JOIN instead — same result.
--
-- Business question: "Which marketing channels generate bookings most
-- cost-effectively, and are any channels going quiet?" (docs/business_problem.md, Q3)

SELECT
    mc.channel_name,
    mc.channel_type,
    d.year,
    d.month,
    COALESCE(SUM(fm.conversions), 0) AS conversions,
    COALESCE(SUM(fm.spend), 0)        AS spend,
    COALESCE(SUM(fm.revenue), 0)       AS revenue
FROM FactMarketing fm
JOIN DimDate d ON fm.month_date_id = d.date_id
RIGHT JOIN DimMarketingChannel mc ON fm.channel_id = mc.channel_id
GROUP BY mc.channel_name, mc.channel_type, d.year, d.month
ORDER BY d.year, d.month, mc.channel_name;