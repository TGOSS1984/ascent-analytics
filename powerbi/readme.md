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

**Import each CSV individually — do not use the "Folder" connector.** In Power BI Desktop: **Get Data → Text/CSV** (not "Folder"). In the file browser, select all 16 files in `powerbi/data_export/` at once (click the first, then Ctrl+click or Shift+click the rest) and Open — Power BI Desktop loads each as its own separate table, named after the file. If your version only supports single-file selection there, just repeat **Get Data → Text/CSV** once per file instead.

It's tempting to use **Get Data → Folder** and point it at `powerbi/data_export/` in one go — don't. The Folder connector is built for combining many files that all share the *same* columns (e.g. 12 identical monthly exports); it loads the whole folder as one table listing file metadata (name, path, a binary blob per file), not one table per file. Since our 16 CSVs each have completely different columns, that's the wrong shape entirely. If you've already done this, delete that query (right-click it in the Queries pane → Delete) and re-import with Text/CSV instead.

Power BI will infer types reasonably well from the CSVs, but check these explicitly in Power Query before loading:

- `DimDate.full_date`, `FactBookings.tour_date_id`/`created_date_id` etc. — these `*_date_id` columns are `YYYYMMDD` integers (e.g. `20240615`), not dates. Leave them as whole numbers; they're join keys, not display fields.
- `*_id` columns generally → **Whole Number**
- Boolean-looking columns (`is_weekend`, `active`, `is_featured`, `storm_warning`, `would_recommend`, equipment flags) → Power BI reads SQLite's 0/1 as whole numbers; convert to **True/False** in Power Query (Transform → Data Type → True/False) so slicers and DAX logic read naturally.
- Currency columns (`total_price`, `revenue`, `spend`, `day_rate_gbp`, `hire_revenue`, `amount`) → **Fixed Decimal Number**, then format as currency (£) in the model view.

## 2. Relationships

This starts as a direct translation of the foreign keys enforced in `sql/schema/02_facts.sql`, but two of them end up different from the SQL schema once built in Power BI — both explained below the table, and both were discovered by actually building this (not guessed in advance), so don't be surprised if Autodetect or your own first pass lands somewhere slightly different too.

All relationships are **one-to-many, single direction** (dimension → fact) unless noted.

| From (dimension) | To (fact) | Status | Notes |
|---|---|---|---|
| DimRegion.region_id | FactBookings.region_id | **Inactive** | See "Why FactBookings→DimRegion is inactive" below |
| DimRoute.region_id | DimRegion.region_id | **Active** | Carries region filtering for FactBookings instead — see below |
| DimRoute.route_id | FactBookings.route_id | Active | |
| DimGuide.guide_id | FactBookings.guide_id | Active | Guide is nullable on some bookings — this is fine, Power BI handles it |
| DimGuide.primary_region_id | DimRegion.region_id | Active | |
| DimCustomer.customer_id | FactBookings.customer_id | Active | |
| DimMarketingChannel.channel_id | FactBookings.channel_id | Active | Nullable |
| DimDate.date_id | FactBookings.tour_date_id | **Active** | See role-playing dates below |
| DimDate.date_id | FactBookings.created_date_id | **Inactive** | |
| FactBookings.booking_id | FactPayments.booking_id | Active | 1:1 |
| FactBookings.booking_id | FactReviews.booking_id | Active | 1:1 (subset — not every booking has a review) |
| FactBookings.booking_id | FactEquipmentHire.booking_id | Active | 1:1 (subset) |
| DimDate.date_id | FactPayments.paid_date_id | **Inactive** | See role-playing dates below |
| DimDate.date_id | FactPayments.refunded_date_id | **Inactive** | |
| DimMarketingChannel.channel_id | FactMarketing.channel_id | Active | |
| DimDate.date_id | FactMarketing.month_date_id | Active | |
| DimMarketingChannel.channel_id | FactWebsiteAnalytics.channel_id | Active | |
| DimDate.date_id | FactWebsiteAnalytics.week_date_id | Active | |
| DimRegion.region_id | FactWeather.region_id | Active | |
| DimDate.date_id | FactWeather.date_id | Active | |

### Why FactBookings → DimRegion is inactive

The SQL warehouse deliberately denormalises `region_id` directly onto `FactBookings` (see `docs/architecture/README.md`) — that's still true and still useful for hand-written SQL. But in Power BI, `DimRoute` separately needs its own path to `DimRegion` (for a `RELATED()` calculated column and the Region → Route hierarchy in step 4 below). Power BI only allows one *active* relationship between any two tables, and `FactBookings → DimRoute → DimRegion` already exists as an indirect path once `DimRoute → DimRegion` is active — so the direct `FactBookings → DimRegion` link has to stay inactive to avoid an ambiguous-path error. **This doesn't lose you anything**: filtering `FactBookings` by region still works exactly the same from a report-building perspective, Power BI just resolves it through the extra hop automatically.

### Role-playing dates

`FactBookings` has two dates (tour date, created date) and `FactPayments` has two (paid, refunded) — plus `FactPayments` is 1:1 with `FactBookings`, which already has an active path to `DimDate`. That means **all three** of `created_date_id`, `paid_date_id`, and `refunded_date_id` need to stay **inactive** — if any of them were active, there'd be two ways to reach `DimDate` from `FactBookings` (directly, or via that column), which Power BI won't allow. The measures that genuinely need one of these secondary dates use `USERELATIONSHIP()` to activate it temporarily just for that calculation — see `dax_measures.md`.

## 3. Mark DimDate as the date table

Model view → select `DimDate` → **Mark as date table** → choose `full_date`. This unlocks Power BI's built-in time-intelligence functions (`TOTALYTD`, `SAMEPERIODLASTYEAR`, etc.) used in several measures.

## 4. Hierarchies

**Dragging fields to build a hierarchy doesn't always work reliably** — if it doesn't respond for you, use right-click instead, which is more consistent: right-click the field you want to add → **Add to hierarchy** → pick the hierarchy from the submenu.

- **DimDate**: right-click `Year` → Create hierarchy. Then right-click `Quarter` → Add to hierarchy → your new hierarchy; repeat for `Month Name`, then `Day`. Gives you a standard Year → Quarter → Month → Day drill-down.
- **DimRoute → DimRegion**: hierarchies can only live inside a single table, so a "Region → Route" drill-down can't be built by connecting `DimRegion` and `DimRoute` directly — instead, add a calculated column on `DimRoute` first (see step 5), then build the hierarchy on `DimRoute` alone, using that calculated column as the parent level and the route name as the child level.
- **DimGuide**: no natural hierarchy (flat list), but consider grouping by `employment_type` as a secondary slicer.

## 5. Calculated columns

Almost everything needed already exists as a real column from the warehouse (that's the point of building the star schema properly first) — but a few are naturally calculated *in* Power BI rather than the warehouse, since they're presentation concerns:

```dax
DimRoute[Region Name] = RELATED(DimRegion[name])
```

This is what makes the Region → Route hierarchy in step 4 possible — it pulls the region name onto `DimRoute` using the `DimRoute → DimRegion` relationship from step 2, so the hierarchy can live entirely within `DimRoute`.

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

## 6. Apply the Ascent Analytics theme

[`ascent_analytics_theme.json`](ascent_analytics_theme.json) is a custom report theme derived directly from **UK Summit Guides' own design tokens** (`frontend/src/styles/tokens.css`) — the same dark, moody mountain aesthetic as the live booking site, so a recruiter clicking between the two projects sees one consistent visual identity, not two unrelated builds.

**Apply it:** View tab → Themes → Browse for themes → select `ascent_analytics_theme.json`.

### Where the colours came from

| Theme role | Colour | Source in `tokens.css` |
|---|---|---|
| Report background | `#0C1D29` | `--color-bg-alt` (winter) |
| Page canvas | `#07131C` | `--color-bg` (winter) |
| Foreground / text | `#EEF3F6` | `--color-text` (winter) |
| Table accent | `#B0CFD0` | `--color-accent` (winter) |
| "Good" (positive KPI) | `#7FBF8C` | new — a muted green consistent with the palette's desaturated tone |
| "Neutral" | `#D6C18E` | `--color-accent` (summer) |
| "Bad" (negative KPI) | `#C1666B` | new — a muted brick red, avoiding a jarring bright red against the dark palette |
| Diverging max | `#8FE3FF` | `--motif-route-glow` (winter) |
| Diverging min | `#FFD27A` | `--motif-route-glow` (summer) |

The 10-colour categorical palette (used for routes, regions, channels, etc.) deliberately **alternates winter and summer tones** — the same cool/warm contrast the live site uses when a visitor toggles between its two seasonal themes:

`#B0CFD0` (winter) → `#D6C18E` (summer) → `#8FE3FF` (winter) → `#C7B06A` (summer) → `#7F9499` (winter) → `#A8B48A` (summer) → `#91A8B2` (winter) → `#BDC0AE` (summer) → `#405664` (winter) → `#6A8A72` (summer)

Typography is set to **Inter** throughout, matching `--font-sans` in the same tokens file. Card and table visuals pick up rounded borders and a translucent dark background echoing the site's `--radius-md` panel styling.

If a chart ever needs more than 10 distinct categories, Power BI will start blending/repeating theme colours — for high-cardinality visuals (e.g. all 30 routes on one chart), consider grouping into top-N + "Other" rather than fighting the palette.

Next: [`dax_measures.md`](dax_measures.md) for the full measure library.