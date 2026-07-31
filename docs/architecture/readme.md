# Architecture

## Pipeline

```
Raw Data (CSV, synthetic + intentionally messy)
        │  src/generation/
        ▼
Python Cleaning & Validation
        │  src/cleaning/
        ▼
SQL Warehouse — Star Schema (SQLite)
        │  sql/schema/ + src/warehouse/
        ▼
Power BI Semantic Model + DAX
        │
        ▼
Executive & Departmental Dashboards
```

## Star schema

The warehouse is a Kimball-style star schema: one row per business event in each fact table, surrounded by dimension tables that describe the who/what/where/when of that event.

```
                         DimDate
                            │
DimCustomer ─── FactBookings ─── DimRoute ─── DimRegion
                    │    │            │
                    │    └── DimGuide │
                    │                 │
              FactPayments      FactReviews
                                      │
                              FactEquipmentHire

DimMarketingChannel ─── FactMarketing
                    └─── FactWebsiteAnalytics

DimRegion ─── FactWeather ─── DimDate
```

### Dimensions

| Table | Grain | Notes |
|---|---|---|
| DimDate | one row per calendar day | Spans the full 2019-2025 window; includes both a standard meteorological calendar season (for general time intelligence) and is distinct from the booking-specific `season` field (winter/summer only), which stays a degenerate attribute on FactBookings — see below |
| DimRegion | one row per region | Aligned to `Region` |
| DimGuide | one row per guide | Aligned to `Guide`, with `primary_region_id` resolved to a real FK |
| DimRoute | one row per route | Aligned to `Route`, with `region_id` resolved to a real FK |
| DimCustomer | one row per **unique contact email** | **Derived, not sourced** — the real UK Summit Guides schema has no `Customer` entity; `Booking` only stores contact details inline. The warehouse derives a customer dimension by grouping bookings on `contact_email`, since that's the only stable identifier available. This is a real, common warehouse-design situation (the source system wasn't built with analytics in mind) and is documented here rather than glossed over |
| DimMarketingChannel | one row per channel | organic / direct / referral / paid_search / paid_social / email, with a `channel_type` (paid/unpaid) grouping attribute |

### Facts

| Table | Grain | Key measures |
|---|---|---|
| FactBookings | one row per booking | `party_size`, `total_price`, `lead_time_days` |
| FactPayments | one row per payment (1:1 with booking) | `amount` |
| FactReviews | one row per review (subset of bookings) | `overall_rating`, `guide_rating`, `route_rating`, `safety_rating`, `value_rating`, `comment_length` |
| FactEquipmentHire | one row per booking with equipment hired | `hire_revenue`, plus boolean flags per item |
| FactMarketing | one row per campaign/channel/month | `spend`, `clicks`, `impressions`, `conversions`, `revenue` |
| FactWebsiteAnalytics | one row per week/traffic-source/device | `sessions`, `users`, `bounce_rate`, `conversion_rate` |
| FactWeather | one row per date/region | `temperature_c`, `rain_mm`, `wind_speed_kmh`, `visibility_km`, `snow_depth_cm`, `storm_warning` |

### Deliberate modelling decisions

- **`region_id` is denormalised onto `FactBookings`.** Strict Kimball practice would only carry `route_id` and require a join through `DimRoute` to reach region. Region is filtered on constantly (most dashboards slice by region first), so it's carried directly on the fact table as a documented denormalisation, not an oversight.
- **`season` stays a degenerate dimension on `FactBookings`** rather than becoming its own table — it's a two-value attribute (`winter`/`summer`) sourced directly from `ScheduledTour`, and a full dimension table for two values would add a join with no analytical benefit.
- **`DimCustomer` stores identity fields only** (email, latest name, latest phone) — not rebooking counts or lifetime value. Those are measures, calculated from `FactBookings` in DAX, not facts stored redundantly inside a dimension.
- **No `DimTour` table.** A `ScheduledTour` is really an event that generates `FactBookings` rows, not a describable "thing" beyond the route/guide/date/season it already carries — so those attributes live directly on the fact table rather than behind an extra join.