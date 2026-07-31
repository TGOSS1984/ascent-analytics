# KPI Catalogue

Every KPI below will be implemented as a Power BI DAX measure once the semantic model is built (tracked in the README roadmap). Each entry defines: what it means, how it's calculated, the grain it's reported at, and which warehouse table(s) it draws from — so there's a single source of truth rather than metrics being redefined per dashboard.

Source tags: **[Core]** = built from data aligned to the real UK Summit Guides schema. **[Ext]** = built from a synthetic extension table (marketing, weather, equipment, reviews).

---

## 1. Executive Dashboard

| KPI | Definition | Formula | Grain | Source |
|---|---|---|---|---|
| Revenue | Total confirmed booking revenue | `SUM(Booking.total_price)` where status = confirmed | Day/Month/Year | FactBookings [Core] |
| Net Profit | Revenue minus guide cost and equipment cost | `Revenue - GuideCost - EquipmentCost` | Month/Year | FactBookings, FactGuideCost, FactEquipment [Core/Ext] |
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
| Revenue by Season | Revenue split by winter/summer | `SUM(total_price)` grouped by Season | Season | FactBookings → DimTour [Core] |
| Revenue Growth % | Period-over-period revenue change | `(Revenue_current - Revenue_prior) / Revenue_prior` | Month/Year | derived |
| Average Booking Value | Mean revenue per booking | `Revenue / Bookings` | Month | derived |
| Average Revenue Per Guide-Day | Revenue generated per guide day worked | `Revenue / Guide-days worked` | Guide/Month | FactBookings, FactGuideAvailability [Core] |

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
| Guide Utilisation % | Days worked vs days available | `Days Worked / Days Available` | Guide/Month | FactGuideAvailability, FactBookings [Core] |
| Revenue Generated per Guide | Total revenue attributable to a guide's tours | `SUM(total_price)` grouped by Guide | Guide | FactBookings [Core] |
| Average Guide Rating | Mean guide-specific review score | `AVG(Review.guide_rating)` | Guide | FactReviews [Ext] |
| Average Safety Rating | Mean safety review score | `AVG(Review.safety_rating)` | Guide | FactReviews [Ext] |
| Guide Performance Index | Composite score blending rating, utilisation, and cancellation rate | weighted composite (documented in DAX) | Guide | derived |
| Guide Cancellation % | % of a guide's scheduled tours cancelled | `Cancelled tours / Total scheduled tours` | Guide | FactBookings, ScheduledTour [Core] |

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
| Weather-Related Cancellation % | Cancellations attributable to adverse weather | `Weather-flagged cancellations / Total cancellations` | Month | FactBookings, FactWeather [Core/Ext] |
| Equipment Hire Rate | % of bookings with any equipment hired | `Bookings with hire / Total bookings` | Month | FactEquipment [Ext] |
| Equipment Revenue | Total revenue from equipment hire | `SUM(hire_revenue)` | Month | FactEquipment [Ext] |
| Storm-Warning Days per Region | Count of days with a storm warning flag | `COUNT(days)` where storm_warning = true, by Region | Region/Month | FactWeather [Ext] |
| Guide Availability % | Guides marked available vs total roster | `Available guide-days / Total guide-days` | Month | FactGuideAvailability [Core] |

## 8. Finance Dashboard

| KPI | Definition | Formula | Grain | Source |
|---|---|---|---|---|
| Gross Margin | Revenue minus direct guide/equipment cost | `Revenue - Direct Costs` | Month | FactBookings, FactGuideCost [Core] |
| Refund % | % of paid bookings refunded | `Refunded Payments / Paid Payments` | Month | FactPayments [Core] |
| Payment Success Rate | % of payment attempts that succeed | `Paid / (Paid + Failed)` | Month | FactPayments [Core] |
| Outstanding Balance | Sum of pending payments | `SUM(amount)` where status = pending | Point-in-time | FactPayments [Core] |
| Average Refund Value | Mean refund amount | `AVG(amount)` where status = refunded | Month | FactPayments [Core] |

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