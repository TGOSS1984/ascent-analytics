# Analytical Query Library

Runnable SQL answering the core business questions from [`docs/business_problem.md`](../../docs/business_problem.md), against the star schema in `sql/schema/`. Run after `python -m src.warehouse.build_warehouse` and `python -m src.warehouse.apply_views` (query 06 depends on `vw_weather_flagged_cancellations`).

| File | Business question | SQL techniques demonstrated |
|---|---|---|
| `01_revenue_by_region.sql` | Which regions are most profitable, and where's cancellation worth investigating? | `INNER JOIN`, `GROUP BY`, `HAVING`, `CASE` |
| `02_top_routes_by_region.sql` | Which routes are most profitable within each region? | CTE, `RANK() OVER (PARTITION BY ...)` |
| `03_guide_leaderboard.sql` | Which guides perform best, region by region? | CTE, `ROW_NUMBER()`, `LEFT JOIN`, `NULLIF` |
| `04_month_over_month_growth.sql` | How is the business growing, and where are the shocks? | CTE, `LAG()`, percentage-change calculation |
| `05_repeat_customer_intervals.sql` | Which customers return, and how long's the gap? | CTE, `LEAD()`, `ROW_NUMBER()` |
| `06_cancellation_drivers.sql` | What causes cancellations, and which weather conditions matter? | `CASE` bucketing, view composition |
| `07_marketing_channel_mix.sql` | Which channels are working, including ones that went quiet? | `RIGHT JOIN`, `COALESCE` |
| `08_cohort_retention.sql` | How strong is retention by acquisition cohort? | Multiple chained CTEs, conditional aggregation |

A couple of version notes, both called out in the relevant file:
- `07_marketing_channel_mix.sql` uses `RIGHT JOIN`, which needs SQLite 3.39+ (2022) — swap the join order and use `LEFT JOIN` if your SQLite build is older.
- `src/warehouse/procedures.py` uses the `FILTER (WHERE ...)` clause on an aggregate, which needs SQLite 3.30+ (2019) — both should be well within range for any current Python install.