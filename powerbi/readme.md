# Power BI Setup Guide

This walks through turning the exported star schema into a working Power BI semantic model: importing data, wiring up relationships, marking the date table, and building the hierarchies most dashboards will need. DAX measures are documented separately in [`dax_measures.md`](dax_measures.md).

## 1. Get the data into Power BI

Run the export script first (after the warehouse is built):

```bash
python -m src.warehouse.build_warehouse
python -m src.warehouse.export_for_powerbi
```

This writes 16 CSVs to `powerbi/data_export/`: the 13 star-schema dimension/fact tables, plus 3 pre-aggregated summary tables (`Summary_CustomerLTV.csv`, `Summary_GuidePerformance.csv`, `Summary_RoutePerformance.csv`) exported from the SQL views built in commit 9. These summary tables load as standalone tables, not related to anything else — they're for dropping straight into a visual (e.g. a customer LTV table) without re-deriving the calculation in DAX, since the SQL already did it once, correctly, and there's no reason to do it twice.

**Why CSV export rather than a live SQLite connection?** Power BI Desktop has no built-in SQLite connector. The only way in is a third-party ODBC driver (e.g. [sqliteodbc](http://www.ch-werner.de/sqliteodbc/)), which means installing a driver, configuring a DSN, and troubleshooting connection strings — real friction for a single-user, file-based database that isn't going to be queried concurrently by anyone else anyway. CSV import is what most real Power BI projects against a SQLite or file-based source actually do, and it keeps this project's Windows setup story simple after everything else we've already worked through together.

*(If you do want a live connection — useful if you plan to refresh the warehouse and re-import without re-mapping anything — install the SQLite ODBC driver, create a User DSN pointing at `data/warehouse/ascent_analytics.db`, then in Power BI: Get Data → ODBC → select the DSN. Everything else in this guide (relationships, hierarchies, measures) is identical either way.)*

In Power BI Desktop: **Get Data → Text/CSV**, import all 13 files from `powerbi/data_export/`. Power BI will infer types reasonably well from the CSVs, but check these explicitly in Power Query before loading:

- `DimDate.full_date`, `FactBookings.tour_date_id`/`created_date_id` etc. — these `*_date_id` columns are `YYYYMMDD` integers (e.g. `20240615`), not dates. Leave them as whole numbers; they're join keys, not display fields.
- `*_id` columns generally → **Whole Number**
- Boolean-looking columns (`is_weekend`, `active`, `is_featured`, `storm_warning`, `would_recommend`, equipment flags) → Power BI reads SQLite's 0/1 as whole numbers; convert to **True/False** in Power Query (Transform → Data Type → True/False) so slicers and DAX logic read naturally.
- Currency columns (`total_price`, `revenue`, `spend`, `day_rate_gbp`, `hire_revenue`, `amount`) → **Fixed Decimal Number**, then format as currency (£) in the model view.

## 2. Relationships

This is a direct translation of the foreign keys already enforced in `sql/schema/02_facts.sql` — Power BI's Model view just needs them drawn explicitly. All relationships below are **one-to-many, single direction** (dimension → fact) unless noted.

| From (dimension) | To (fact) | Notes |
|---|---|---|
| DimRegion.region_id | FactBookings.region_id | |
| DimRoute.route_id | FactBookings.route_id | |
| DimGuide.guide_id | FactBookings.guide_id | Guide is nullable on some bookings — this is fine, Power BI handles it |
| DimCustomer.customer_id | FactBookings.customer_id | |
| DimMarketingChannel.channel_id | FactBookings.channel_id | Nullable |
| **DimDate.date_id** | **FactBookings.tour_date_id** | **Active** relationship — see role-playing dates below |
| DimDate.date_id | FactBookings.created_date_id | **Inactive** — see below |
| FactBookings.booking_id | FactPayments.booking_id | 1:1, but model as one-to-many for consistency |
| FactBookings.booking_id | FactReviews.booking_id | 1:1 (subset — not every booking has a review) |
| FactBookings.booking_id | FactEquipmentHire.booking_id | 1:1 (subset) |
| DimDate.date_id | FactPayments.paid_date_id | **Active** |
| DimDate.date_id | FactPayments.refunded_date_id | **Inactive** |
| DimMarketingChannel.channel_id | FactMarketing.channel_id | |
| DimDate.date_id | FactMarketing.month_date_id | |
| DimMarketingChannel.channel_id | FactWebsiteAnalytics.channel_id | |
| DimDate.date_id | FactWebsiteAnalytics.week_date_id | |
| DimRegion.region_id | FactWeather.region_id | |
| DimDate.date_id | FactWeather.date_id | |

### Role-playing dates

`FactBookings` has two dates (when the tour happened, when the booking was made) and `FactPayments` has two (when paid, when refunded). Power BI only allows one **active** relationship between any pair of tables — set the primary business date active (tour date, paid date) and leave the secondary one inactive. Measures that need the secondary date use `USERELATIONSHIP()` explicitly — see `dax_measures.md` for the handful of measures that do this (e.g. booking lead time, refund timing).

## 3. Mark DimDate as the date table

Model view → select `DimDate` → **Mark as date table** → choose `full_date`. This unlocks Power BI's built-in time-intelligence functions (`TOTALYTD`, `SAMEPERIODLASTYEAR`, etc.) used in several measures.

## 4. Hierarchies

Build these in Model view by dragging one field onto another:

- **DimDate**: `Year` → `Quarter` → `Month Name` → `Day` (a standard calendar drill-down)
- **DimRegion → DimRoute**: `Region Name` → `Route Name` (drag `name` from DimRoute onto `DimRegion.name` after relating them via the fact table, or create a calculated hierarchy in the visual directly — routes already carry `region_id`, so this works as a two-level slicer hierarchy on most visuals)
- **DimGuide**: no natural hierarchy (flat list), but consider grouping by `employment_type` as a secondary slicer

## 5. Calculated columns

Almost everything needed already exists as a real column from the warehouse (that's the point of building the star schema properly first) — but a few are naturally calculated *in* Power BI rather than the warehouse, since they're presentation concerns:

```dax
FactBookings[Lead Time Bucket] =
SWITCH(
    TRUE(),
    FactBookings[lead_time_days] <= 7, "0-7 days",
    FactBookings[lead_time_days] <= 30, "8-30 days",
    FactBookings[lead_time_days] <= 90, "31-90 days",
    "90+ days"
)
```

```dax
DimGuide[Experience Band] =
SWITCH(
    TRUE(),
    DimGuide[years_experience] < 5, "Junior (<5 yrs)",
    DimGuide[years_experience] < 15, "Experienced (5-15 yrs)",
    "Veteran (15+ yrs)"
)
```

Next: [`dax_measures.md`](dax_measures.md) for the full measure library.