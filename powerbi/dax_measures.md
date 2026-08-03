# DAX Measure Library

Every measure below assumes the relationships and role-playing date setup from [`README.md`](README.md) are already in place. Organised by dashboard, mirroring [`docs/kpi_catalogue/README.md`](../docs/kpi_catalogue/README.md) — cross-reference that file for the plain-English definition and grain of each KPI; this file is the DAX implementation.

A few conventions used throughout:
- `DIVIDE(a, b)` instead of `a / b` everywhere, so a zero denominator returns blank instead of an error.
- "Confirmed" revenue always means `FactBookings[status] = "confirmed"` — `amended` bookings are excluded from revenue by convention here since their price may not reflect the final agreed amount; adjust if the business wants amended included.
- Measures that need a second date relationship use `USERELATIONSHIP()` explicitly and are commented as such.

---

## Base measures (reused everywhere)

```dax
Total Bookings = COUNTROWS(FactBookings)

Confirmed Bookings =
CALCULATE([Total Bookings], FactBookings[status] = "confirmed")

Cancelled Bookings =
CALCULATE([Total Bookings], FactBookings[status] = "cancelled")

Revenue =
CALCULATE(SUM(FactBookings[total_price]), FactBookings[status] = "confirmed")

Cancellation Rate =
DIVIDE([Cancelled Bookings], [Total Bookings])

Average Booking Value =
DIVIDE([Revenue], [Confirmed Bookings])

-- Guide-days worked: distinct (guide, tour) combinations where at least
-- one booking on that tour wasn't cancelled. This is a documented proxy,
-- not a direct tour-level fact — the warehouse's fact grain is Booking,
-- not ScheduledTour, so a tour with zero bookings ever made is invisible
-- to this measure. In practice very few such tours exist (the generator
-- cancels most empty-published tours outright — see docs/data_dictionary).
-- CORRECTED — originally used FactBookings[tour_id], which overcounts
-- whenever a guide leads two different tours on the same calendar date
-- (two tour_ids, one real day). Counting tour_date_id instead correctly
-- caps a "guide-day" at one per actual calendar day. This was caught
-- live when Guide Utilisation % came back above 100% for a guide with a
-- lot of same-day double-bookings — a logical impossibility that
-- surfaced the bug immediately once cross-checked.
Guide-Days Worked =
CALCULATE(
    DISTINCTCOUNT(FactBookings[tour_date_id]),
    FactBookings[status] <> "cancelled"
)

Guide Cost =
SUMX(
    SUMMARIZE(
        FILTER(FactBookings, FactBookings[status] <> "cancelled"),
        FactBookings[guide_id],
        FactBookings[tour_date_id]
    ),
    LOOKUPVALUE(DimGuide[day_rate_gbp], DimGuide[guide_id], FactBookings[guide_id])
)

Equipment Hire Revenue =
SUM(FactEquipmentHire[hire_revenue])

Total Revenue (incl. equipment) =
[Revenue] + [Equipment Hire Revenue]
```

## 1. Executive Dashboard

```dax
Net Profit =
[Total Revenue (incl. equipment)] - [Guide Cost]

Net Profit Margin =
DIVIDE([Net Profit], [Total Revenue (incl. equipment)])

Average Customer Satisfaction =
AVERAGE(FactReviews[overall_rating])

-- A customer counts as "repeat" if they have more than one confirmed/
-- amended booking anywhere (not just in the current filter context) —
-- this intentionally looks at the customer's whole history.
Repeat Customers =
CALCULATE(
    DISTINCTCOUNT(FactBookings[customer_id]),
    FILTER(
        VALUES(FactBookings[customer_id]),
        CALCULATE(
            COUNTROWS(FactBookings),
            ALL(FactBookings[status]),
            FactBookings[status] IN {"confirmed", "amended"}
        ) > 1
    )
)

Total Customers = DISTINCTCOUNT(FactBookings[customer_id])

Repeat Customer Rate = DIVIDE([Repeat Customers], [Total Customers])
```

## 2. Sales Dashboard

```dax
-- Requires DimDate marked as the date table (see README.md step 3)
Revenue PY =
CALCULATE([Revenue], SAMEPERIODLASTYEAR(DimDate[full_date]))

Revenue Growth % =
DIVIDE([Revenue] - [Revenue PY], [Revenue PY])

Revenue per Guide-Day =
DIVIDE([Revenue], [Guide-Days Worked])

Revenue YTD =
TOTALYTD([Revenue], DimDate[full_date])
```

Revenue/bookings by region, route, or season don't need their own measures — drop `[Revenue]` or `[Confirmed Bookings]` into a matrix visual with `DimRegion[name]`, `DimRoute[name]`, or `FactBookings[season]` on rows; the relationships do the filtering.

### Week and day analysis (bank holidays, weekends, popular days)

`DimDate` carries a retail week (Sunday → Saturday) and bank holiday/summer holiday flags — see `docs/data_dictionary/README.md` for the full field list. No new measures needed, just new ways to slice `[Revenue]`/`[Confirmed Bookings]`:

- **Popular weeks (bank holiday weekends, etc.):** matrix or line chart with `DimDate[week_start_date]` (or `DimDate[week_number]` + `DimDate[retail_year]`) on rows/axis, `[Revenue]` on values. Bank holiday weeks should visibly spike.
- **Weekday vs weekend pattern:** column chart, axis `DimDate[day_name]` (remember to set its Sort by Column to `day_of_week` first, or it'll sort alphabetically — see the polish-stage note in `README.md`), values `[Revenue]`.
- **Is this a bank holiday or summer holiday?** Slicer or filter on `DimDate[is_bank_holiday]` / `DimDate[is_summer_holiday]` — useful for isolating "what does a normal week look like" from the spikes when eyeballing trends.

If you want an explicit "% uplift on bank holidays" figure rather than just an eyeballed chart:

```dax
Revenue on Bank Holidays vs Regular Days =
VAR BankHolidayRevenue = CALCULATE([Revenue], DimDate[is_bank_holiday] = TRUE())
VAR RegularDayRevenue = CALCULATE([Revenue], DimDate[is_bank_holiday] = FALSE())
VAR BankHolidayDays = CALCULATE(DISTINCTCOUNT(DimDate[date_id]), DimDate[is_bank_holiday] = TRUE())
VAR RegularDays = CALCULATE(DISTINCTCOUNT(DimDate[date_id]), DimDate[is_bank_holiday] = FALSE())
RETURN DIVIDE(DIVIDE(BankHolidayRevenue, BankHolidayDays), DIVIDE(RegularDayRevenue, RegularDays)) - 1
```

## 3. Customer Dashboard

For customer lifetime value, first/last booking date, and the repeat-customer flag at the individual-customer grain, use **`Summary_CustomerLTV`** (imported from `vw_customer_summary`) directly in a table visual rather than recomputing in DAX — it's already correct and tested (see `tests/test_views_and_procedures.py`).

**Heads up: this DAX `Repeat Customer Rate` and `Summary_CustomerLTV[is_repeat_customer]` measure different things, on purpose — they will not agree, and that's not a bug.** The DAX version only counts a customer as "repeat" if they have 2+ **confirmed or amended** bookings (they actually completed more than one trip). The SQL view counts 2+ bookings of **any status**, including ones later cancelled (they *attempted* to book more than once). Found by cross-checking both on the same dashboard — they came back as 3.9% vs 5.09% on one test run, which is the expected gap, not an error. If displaying both, label them distinctly (e.g. rename the SQL-based chart's legend to "Made 2+ Booking Attempts") so it doesn't read as a bug to whoever's looking at the dashboard.

```dax
New Customers =
CALCULATE(
    DISTINCTCOUNT(FactBookings[customer_id]),
    FILTER(
        VALUES(FactBookings[customer_id]),
        CALCULATE(MIN(FactBookings[tour_date_id])) >= MIN(FactBookings[tour_date_id])
    )
)
-- Simpler in practice: use Summary_CustomerLTV[first_booking_date] filtered
-- to the current period — this DAX-only version is included to show the
-- pattern, but the SQL-precomputed version is what the dashboard should use.

Average Reviews per Confirmed Booking =
DIVIDE(COUNTROWS(FactReviews), [Confirmed Bookings])
```

## 4. Guide Dashboard

For guide-level bookings, revenue, average rating, and cancellation rate, use **`Summary_GuidePerformance`** (from `vw_guide_performance`) directly — same reasoning as the customer summary above.

```dax
-- CORRECTED — the original version of this measure used DATEDIFF()
-- directly on tour_date_id, which is an integer (20240615), not a real
-- date, and variable names FirstDate/LastDate, which collide with DAX's
-- own FIRSTDATE()/LASTDATE() functions and produce confusing cascading
-- syntax errors. Both were caught live while building this dashboard —
-- fixed here so the docs match what's actually verified working.
Guide Utilisation % =
VAR ActiveDates = CALCULATETABLE(VALUES(DimDate[full_date]), FactBookings)
VAR EarliestActiveDate = MINX(ActiveDates, DimDate[full_date])
VAR LatestActiveDate = MAXX(ActiveDates, DimDate[full_date])
VAR AvailableDays = DATEDIFF(EarliestActiveDate, LatestActiveDate, DAY) + 1
RETURN DIVIDE([Guide-Days Worked], AvailableDays)

Guide Performance Index =
-- Composite: 40% normalised revenue, 40% average rating (out of 5, scaled
-- to 0-1), 20% inverse cancellation rate. Weights are a documented,
-- adjustable business choice, not a derived statistical model.
VAR RevenueNorm = DIVIDE([Revenue], CALCULATE([Revenue], ALL(DimGuide)))
VAR RatingNorm = DIVIDE(AVERAGE(FactReviews[guide_rating]), 5)
VAR CancellationScore = 1 - [Cancellation Rate]
RETURN
    0.4 * RevenueNorm + 0.4 * RatingNorm + 0.2 * CancellationScore

-- Discount analysis — "which guides discount more, therefore have lower
-- margins?" DimGuide[discount_tendency_pct] is the guide's baseline
-- tendency; these two measures show what actually happened in bookings.
Bookings with Discount % =
DIVIDE(
    CALCULATE(COUNTROWS(FactBookings), FactBookings[discount_applied] = TRUE()),
    [Total Bookings]
)

Average Discount % (Discounted Bookings) =
CALCULATE(
    AVERAGE(FactBookings[discount_pct]),
    FactBookings[discount_applied] = TRUE()
)

Total Discount Given =
SUMX(FactBookings, FactBookings[list_price] - FactBookings[total_price])
```

Each of these three new measures should be dropped into a table alongside `DimGuide[full_name]` and `DimGuide[discount_tendency_pct]` to see the correlation directly — a guide with a higher tendency should show a visibly higher `Bookings with Discount %`.

## 5. Route / Tour Performance Dashboard

For route-level bookings, revenue, and average rating, use **`Summary_RoutePerformance`** (from `vw_route_performance`) directly.

**Map visual:** `DimRoute` carries `trailhead_lat`/`trailhead_lon` — real approximate trailhead coordinates for each route, added specifically to support a map visual here. Use the **Map** or **ArcGIS Map** visual: Latitude → `trailhead_lat`, Longitude → `trailhead_lon`, Legend or Tooltips → `DimRoute[name]`, bubble size → `[Revenue]` (or `[Confirmed Bookings]`). This gives a genuinely useful "where's the money coming from geographically" view rather than just the region-level bar chart. Note difficulty also now measurably affects rating and cancellation rate (see `docs/data_dictionary/README.md`) — earlier versions of the dataset had these flat across difficulty tiers, which is worth knowing if you're comparing against an older screenshot or export.

```dax
Occupancy % =
-- Booked party size vs the route's typical max group size, averaged
-- across confirmed bookings — a proxy for "how full tours tend to run"
-- at the fact grain available (see Guide-Days Worked note on the
-- ScheduledTour/Booking grain gap).
AVERAGEX(
    FILTER(FactBookings, FactBookings[status] = "confirmed"),
    DIVIDE(FactBookings[party_size], 3)  -- 3 = the platform-wide max party size
)
```

## 6. Marketing Dashboard

Most marketing KPIs are cleaner computed in SQL (`vw_marketing_performance`, already built) and imported directly if you want them in Power BI without re-deriving ROAS/CAC in DAX. If computing from `FactMarketing` directly instead:

```dax
Marketing Spend = SUM(FactMarketing[spend])
Marketing Revenue = SUM(FactMarketing[revenue])
Marketing Conversions = SUM(FactMarketing[conversions])

ROAS =
DIVIDE([Marketing Revenue], [Marketing Spend])
-- Blank (not zero) for organic/direct/referral, which have zero spend —
-- correct behaviour: ROAS is undefined, not zero, when there's no spend.

CAC =
DIVIDE([Marketing Spend], [Marketing Conversions])
```

## 7. Operations Dashboard

```dax
Equipment Hire Rate =
DIVIDE(COUNTROWS(FactEquipmentHire), [Confirmed Bookings])

Storm Warning Days =
CALCULATE(COUNTROWS(FactWeather), FactWeather[storm_warning] = TRUE())

-- Weather-flagged cancellations: mirrors vw_weather_flagged_cancellations'
-- logic (storm warning OR >15mm rain) but computed in DAX for cases where
-- you want it as a live measure rather than importing the view.
Weather-Flagged Cancellation Rate =
VAR CancelledBookings = CALCULATETABLE(FactBookings, FactBookings[status] = "cancelled")
VAR FlaggedCount =
    COUNTROWS(
        FILTER(
            CancelledBookings,
            CALCULATE(
                COUNTROWS(FactWeather),
                FactWeather[region_id] = FactBookings[region_id],
                FactWeather[date_id] = FactBookings[tour_date_id],
                FactWeather[storm_warning] = TRUE() || FactWeather[rain_mm] > 15
            ) > 0
        )
    )
RETURN DIVIDE(FlaggedCount, COUNTROWS(CancelledBookings))
```

## 8. Finance Dashboard

```dax
Gross Margin = [Revenue] - [Guide Cost]

Refund % =
DIVIDE(
    CALCULATE(COUNTROWS(FactPayments), FactPayments[status] = "refunded"),
    CALCULATE(COUNTROWS(FactPayments), FactPayments[status] = "paid")
)

Payment Success Rate =
DIVIDE(
    CALCULATE(COUNTROWS(FactPayments), FactPayments[status] = "paid"),
    CALCULATE(
        COUNTROWS(FactPayments),
        FactPayments[status] IN {"paid", "failed"}
    )
)

Outstanding Balance =
CALCULATE(SUM(FactPayments[amount]), FactPayments[status] = "pending")

Average Price per Tour =
DIVIDE(SUM(FactBookings[total_price]), [Confirmed Bookings])

-- Company-wide discount impact — how much margin is actually being given
-- away, not just how often it happens (that's the Guide dashboard's job).
-- [Total Discount Given] is already defined on the Guide dashboard above —
-- measures are shared across the whole model once created, so don't
-- recreate it here, just reuse it.
Discount % of Revenue =
DIVIDE([Total Discount Given], SUM(FactBookings[list_price]))

-- Refund timing needs *both* of FactPayments' date relationships
-- activated explicitly via USERELATIONSHIP — paid_date_id turned out to
-- need this too, not just refunded_date_id as originally planned (see
-- powerbi/README.md's "Role-playing dates" section for why: FactPayments
-- is 1:1 with FactBookings, which already has an active path to DimDate,
-- so neither payment date can be the model's default active relationship
-- without creating an ambiguous path).
Average Days to Refund =
AVERAGEX(
    CALCULATETABLE(FactPayments, FactPayments[status] = "refunded"),
    VAR PaidDate =
        CALCULATE(
            MAX(DimDate[full_date]),
            USERELATIONSHIP(FactPayments[paid_date_id], DimDate[date_id])
        )
    VAR RefundedDate =
        CALCULATE(
            MAX(DimDate[full_date]),
            USERELATIONSHIP(FactPayments[refunded_date_id], DimDate[date_id])
        )
    RETURN DATEDIFF(PaidDate, RefundedDate, DAY)
)
```

## 9. Data Quality Dashboard

The Data Quality Dashboard is the one dashboard that reads from **the pipeline's own output**, not the star schema. Import `docs/data_quality/core_pipeline_log.csv` and `docs/data_quality/extension_pipeline_log.csv` as two more tables (they're not related to anything else — they describe the pipeline, not the business). See [`docs/data_quality/README.md`](../docs/data_quality/README.md) for the column definitions.

```dax
Completeness % =
CALCULATE(
    AVERAGE(core_pipeline_log[value]),
    core_pipeline_log[metric] = "completeness"
)

Total Validation Failures =
CALCULATE(
    SUM(core_pipeline_log[value]),
    core_pipeline_log[metric] = "validation_failures"
)

Total Duplicates Removed =
CALCULATE(
    SUM(core_pipeline_log[value]),
    core_pipeline_log[metric] = "duplicates_removed"
)
```