# KPI Catalogue

Every KPI below is implemented as a Power BI DAX measure — the semantic model is built and all 10 dashboards are live. This catalogue defines *what* each metric means, its grain, and which warehouse table(s) it draws from, in plain business terms; [`powerbi/dax_measures.md`](../../powerbi/dax_measures.md) is the authoritative source for the actual DAX implementation of each one, so if the two ever disagree, the DAX file is correct and this one needs updating.

Source tags: **[Core]** = built from data aligned to the real UK Summit Guides schema. **[Ext]** = built from a synthetic extension table (marketing, weather, equipment, reviews, guide discount tendency).

---

## 1. Executive Dashboard

| KPI | Definition | Formula | Grain | Source |
|---|---|---|---|---|
| Revenue | Total confirmed booking revenue | `SUM(Booking.total_price)` where status = confirmed | Day/Month/Year | FactBookings [Core] |
| Net Profit | Revenue plus equipment hire revenue, minus guide cost | `[Total Revenue (incl. equipment)] - [Guide Cost]` — equipment hire is modelled as a revenue line, not a cost, so there's no separate "equipment cost" to subtract | Month/Year | FactBookings, FactEquipmentHire, DimGuide [Core/Ext] |
| Net Profit Margin | Profit as a % of revenue | `Net Profit / Revenue` | Month/Year | derived |
| Bookings | Count of bookings made | `COUNT(Booking.id)` | Day/Month/Year | FactBookings [Core] |
| Cancellation Rate | % of bookings cancelled | `Cancelled Bookings / Total Bookings` | Month/Year | FactBookings [Core] |
| Repeat Customer Rate | % of customers with 2+ bookings | `Customers with >1 booking / Total customers` | Year | FactBookings, DimCustomer [Core] |
| Average Customer Satisfaction | Mean overall review rating | `AVG(Review.overall_rating)` | Month/Year | FactReviews [Ext] |

## 2. Sales Dashboard

| KPI | Definition | Formula | Grain | Source |
|---|---|---|---|---|
| Revenue by Region | Revenue split by route region | `SUM(total_price)` grouped by Region | Region | FactBookings → DimRoute → DimRegion [Core] |
| Revenue by Route | Revenue split by individual route | `SUM(total_price)` grouped by Route | Route | FactBookings → DimRoute [Core] |
| Revenue by Season | Revenue split by winter/summer | `SUM(total_price)` grouped by Season | Season | FactBookings — `season` is a degenerate attribute on the fact table itself, not a separate dimension (see `docs/architecture/README.md`) [Core] |
| Revenue Growth % | Period-over-period revenue change | `(Revenue_current - Revenue_prior) / Revenue_prior`, using `SAMEPERIODLASTYEAR()` | Month/Year | FactBookings → DimDate [Core] |
| Average Booking Value | Mean revenue per booking | `Revenue / Confirmed Bookings` | Month | derived |
| Revenue per Guide-Day | Revenue generated per guide-day worked | `Revenue / Guide-Days Worked` (distinct calendar dates a guide led a tour, not distinct tour instances — see the Guide dashboard's known double-booking fix) | Guide/Month | FactBookings, DimGuide [Core] |
| Revenue by Week | Weekly revenue, retail week (Sunday-Saturday) | `SUM(total_price)` grouped by `week_start_date` | Week | FactBookings → DimDate [Core] |
| Revenue by Day of Week | Weekday vs weekend demand pattern | `SUM(total_price)` grouped by `day_name` | Day | FactBookings → DimDate [Core] |
| Bank Holiday Revenue Uplift | How much more a bank holiday earns vs a regular day, per-day average | `(BankHolidayRevenue/BankHolidayDays) / (RegularDayRevenue/RegularDays) - 1` | Ad hoc | FactBookings → DimDate [Core/Ext — `is_bank_holiday` is a synthetic UK-calendar flag] — verified at ~2.5x on regular weekdays, ~1.7x on weekends |

## 3. Customer Dashboard

| KPI | Definition | Formula | Grain | Source |
|---|---|---|---|---|
| New vs Returning Customers | Split of first-time vs repeat customers | `COUNT DISTINCT CustomerID`, split by prior booking flag | Month | DimCustomer, FactBookings [Core] |
| Customer Lifetime Value (CLV) | Total revenue per customer to date | `SUM(total_price)` grouped by Customer | Customer | FactBookings [Core] |
| Retention Rate | % of customers who booked again within 12 months | cohort-based retention | Cohort/Year | FactBookings [Core] |
| Average Reviews per Customer | Engagement proxy | `COUNT(Review) / COUNT DISTINCT Customer` | Customer | FactReviews [Ext] |
| Customer Acquisition by Marketing Source | New customers attributed to each channel | `COUNT DISTINCT new Customer` grouped by source | Channel/Month | DimCustomer, FactMarketing [Core/Ext] |

## 4. Guide Dashboard

| KPI | Definition | Formula | Grain | Source |
|---|---|---|---|---|
| Guide Utilisation % | Days worked vs days available (approximated as the guide's own earliest-to-latest active date range, since the schema doesn't track explicit rostered availability) | `Guide-Days Worked / Available Days` | Guide | FactBookings, DimDate [Core] |
| Revenue Generated per Guide | Total revenue attributable to a guide's tours | `SUM(total_price)` grouped by Guide | Guide | FactBookings [Core] |
| Average Guide Rating | Mean guide-specific review score | `AVG(Review.guide_rating)` | Guide | FactReviews [Ext] |
| Average Safety Rating | Mean safety review score | `AVG(Review.safety_rating)` | Guide | FactReviews [Ext] |
| Guide Performance Index | Composite score blending revenue, rating, and cancellation rate (**not** utilisation, despite the name — see `powerbi/dax_measures.md`) | `0.4 × RevenueNorm + 0.4 × RatingNorm + 0.2 × (1 − Cancellation Rate)` | Guide | derived |
| Guide Cancellation % | % of a guide's tours cancelled | `Cancelled Bookings / Total Bookings` filtered to the guide | Guide | FactBookings [Core] |
| Guide Discount Tendency | A guide's baseline discount-offering trait | stored directly, not derived | Guide | DimGuide [Ext] — right-skewed: most guides discount rarely, a few noticeably more |
| Bookings with Discount % | Share of a guide's bookings that had any discount applied | `Discounted Bookings / Total Bookings` | Guide | FactBookings [Ext] — verified to correlate positively with Discount Tendency (top guide: 27.7% of bookings discounted; bottom guide: 2.2%) |
| Average Discount % (Discounted Bookings) | Mean discount size, among bookings that had one | `AVG(discount_pct)` where discount_applied = TRUE | Guide | FactBookings [Ext] |

## 5. Route / Tour Performance Dashboard

| KPI | Definition | Formula | Grain | Source |
|---|---|---|---|---|
| Most Popular Route | Highest booking count | `MAX(COUNT(Booking))` by Route | Route | FactBookings [Core] |
| Highest Revenue Route | Highest total revenue | `MAX(SUM(total_price))` by Route | Route | FactBookings [Core] |
| Highest Rated Route | Highest mean route rating | `MAX(AVG(Review.route_rating))` by Route | Route | FactReviews [Ext] |
| Occupancy % | Booked spaces vs max group size, averaged | `AVG(booked_spaces / max_group_size)` | Route/Month | ScheduledTour, FactBookings [Core] |
| Cancellation Rate by Difficulty | Cancellation % split by difficulty tier | `Cancelled / Total` grouped by Difficulty | Difficulty | FactBookings → DimRoute [Core] |
| Satisfaction by Difficulty | Mean rating split by difficulty tier | `AVG(overall_rating)` grouped by Difficulty | Difficulty | FactReviews → DimRoute [Ext/Core] |

## 6. Marketing Dashboard

| KPI | Definition | Formula | Grain | Source |
|---|---|---|---|---|
| ROAS | Return on ad spend | `Campaign Revenue / Campaign Spend` | Campaign/Month | FactMarketing [Ext] |
| CAC | Cost to acquire a new customer | `Spend / New Customers Acquired` | Channel/Month | FactMarketing, DimCustomer [Ext/Core] |
| Conversion Rate | Bookings per marketing-attributed session | `Conversions / Clicks` | Campaign | FactMarketing [Ext] |
| Cost per Booking | Marketing spend per resulting booking | `Spend / Attributed Bookings` | Channel/Month | FactMarketing, FactBookings [Ext/Core] |
| Channel Mix % | Share of bookings by marketing source | `Bookings by source / Total bookings` | Channel | FactBookings [Core] |

## 7. Operations Dashboard

| KPI | Definition | Formula | Grain | Source |
|---|---|---|---|---|
| Weather-Related Cancellation % | Cancellations attributable to adverse weather | `Weather-flagged cancellations / Total cancellations` | Month | FactBookings, FactWeather [Core/Ext] — verified at ~11.5% of all cancellations; this is an analytical join (same date/region as a storm warning or heavy rain), not a claim that weather directly caused each one — see `docs/data_dictionary/README.md` |
| Equipment Hire Rate | % of bookings with any equipment hired | `Bookings with hire / Total bookings` | Month | FactEquipmentHire [Ext] |
| Equipment Revenue | Total revenue from equipment hire | `SUM(hire_revenue)` | Month | FactEquipmentHire [Ext] — verified at ~£254,555 across the full dataset |
| Storm-Warning Days per Region | Count of days with a storm warning flag | `COUNT(days)` where storm_warning = true, by Region | Region/Month | FactWeather [Ext] |
| Guide Utilisation % | Days worked vs days available (see the Guide dashboard's definition above — reused here at company level rather than a separately-built "Guide Availability %") | `Guide-Days Worked / Available Days` | Month | FactBookings, DimDate [Core] |

## 8. Finance Dashboard

| KPI | Definition | Formula | Grain | Source |
|---|---|---|---|---|
| Gross Margin | Revenue minus direct guide cost | `Revenue - Guide Cost` | Month | FactBookings, DimGuide [Core] |
| Refund % | % of paid bookings refunded | `Refunded Payments / Paid Payments` | Month | FactPayments [Core] |
| Payment Success Rate | % of payment attempts that succeed | `Paid / (Paid + Failed)` | Month | FactPayments [Core] |
| Outstanding Balance | Sum of pending payments | `SUM(amount)` where status = pending | Point-in-time | FactPayments [Core] |
| Average Days to Refund | Mean time between payment and refund | `DATEDIFF(paid_date, refunded_date, DAY)`, averaged | Month | FactPayments → DimDate (via `USERELATIONSHIP()` — both date relationships are inactive by default, see `docs/architecture/README.md`) [Core] — *replaces the originally-planned "Average Refund Value" (£ amount), which was never actually built once a timing metric turned out to be more useful* |
| Average Price per Tour | Mean price actually paid per confirmed booking | `SUM(total_price) / Confirmed Bookings` | Month | FactBookings [Core] |
| Total Discount Given | Total £ discounted off list price | `SUM(list_price - total_price)` | Month | FactBookings [Ext] — verified at ~£50,850 across the full dataset, ~0.92% of gross revenue |
| Discount % of Revenue | Discount given as a share of undiscounted (list) revenue | `Total Discount Given / SUM(list_price)` | Month | FactBookings [Ext] |

## 9. Data Quality Dashboard

| KPI | Definition | Formula | Grain | Source |
|---|---|---|---|---|
| Completeness % | Non-null values across key fields | `Non-null cells / Total cells` per table | Table/Run | ETL log |
| Duplicate Rate | Duplicate records identified and removed | `Duplicates removed / Raw row count` | Table/Run | ETL log |
| Validation Failure Rate | Records failing schema/business rule checks | `Failed rows / Total rows` | Table/Run | ETL log |
| Row Counts by Stage | Row count at raw → cleaned → warehouse | count per stage | Table/Run | ETL log |
| ETL Run Duration | Time taken for the pipeline to run | wall-clock time | Run | ETL log |

---

## Notes

- KPIs tagged **[Ext]** rely on synthetic extension tables that do not exist in the live UK Summit Guides platform. They're included to demonstrate broader warehouse and KPI design skills, and are always labelled as such on the dashboards themselves, not just here.
- Composite/derived indices (e.g. Guide Performance Index) will have their exact weighting documented in the DAX measure definitions once built, not just described in prose — so the calculation is fully auditable.