# Data Dictionary

This documents every field in the warehouse: its type, provenance (aligned to the real UK Summit Guides schema, or a synthetic extension), allowed values, and the cleaning rule that resolves it from the raw column. It's filled in incrementally as each entity is built — currently covers the reference data (Region, Guide, Route) generated in `src/generation/generate_reference_data.py`.

Legend: **[Core]** = field exists in the real Django models. **[Ext]** = synthetic field added for richer analytics, does not exist in the live app.

## Region

| Field | Type | Provenance | Notes / cleaning rule |
|---|---|---|---|
| region_id | int | generated surrogate key | |
| name | string | [Core] `routes_app.Region.name` | Raw column `region_name_raw` has inconsistent casing/whitespace — cleaning standardises to title case and strips whitespace |
| slug | string | [Core] `routes_app.Region.slug` | Derived from cleaned name (slugify), not generated raw |

Six regions are modelled: Snowdonia, Lake District, Scottish Highlands, Peak District, Brecon Beacons, Cairngorms.

## Guide

| Field | Type | Provenance | Notes / cleaning rule |
|---|---|---|---|
| guide_id | int | generated surrogate key | Raw data contains ~2% duplicate rows (simulating duplicate submissions) — deduplicated in cleaning |
| first_name | string | [Core] `routes_app.Guide.first_name` | Raw column has inconsistent casing — cleaned to title case |
| last_name | string | [Core] `routes_app.Guide.last_name` | Same as above |
| qualifications | string | [Core] `routes_app.Guide.qualifications` | Free text, semicolon-separated in raw; ~3% missing (null) — flagged, not imputed, since a missing qualification is a real data gap worth surfacing, not guessing |
| active | boolean | [Core] `routes_app.Guide.active` | |
| years_experience | int | [Ext] | Plausible operational field the live app doesn't yet capture |
| languages | string | [Ext] | Semicolon-separated list |
| employment_type | string (`employed`/`freelance`) | [Ext] | Drives guide cost modelling |
| day_rate_gbp | decimal | [Ext] | Raw column has ~2% of values stored as formatted currency strings (e.g. `"£180.00"`, `"GBP 180.00"`) — cleaning parses these back to numeric |
| primary_region | string | [Ext] | FK resolved to Region in cleaning; raw column has casing inconsistencies like the Region table itself |
| discount_tendency_pct | decimal (0-0.25) | [Ext] | A guide's baseline discount-offering tendency — a business question ("which guides offer bigger discounts, therefore lower margins?"), not a real app field. Right-skewed (Beta(1.5, 8) scaled to 0-25%): most guides discount rarely or never, a handful noticeably more. Drives per-booking `discount_pct`/`discount_applied` on Booking — see below |

## Route

| Field | Type | Provenance | Notes / cleaning rule |
|---|---|---|---|
| route_id | int | generated surrogate key | ~1% duplicate rows injected — deduplicated in cleaning |
| name | string | [Core] `routes_app.Route.name` | Casing cleaned |
| region | FK → Region | [Core] `routes_app.Route.region` | Resolved from raw region name text to `region_id` |
| difficulty | string (`moderate`/`hard`/`advanced`) | [Core] `routes_app.Route.difficulty` | Closed enum — raw casing normalised to lowercase to match the real app's choices |
| distance_km | decimal | [Core] `routes_app.Route.distance_km` | ~3% of raw values stored as `"14.5 km"` strings — cleaning strips the unit and casts to numeric |
| duration_hours | decimal | [Core] `routes_app.Route.duration_hours` | |
| mountain_height_m | int | [Core] `routes_app.Route.mountain_height_m` | |
| elevation_gain_m | int | [Core] `routes_app.Route.elevation_gain_m` | ~2% missing in raw — imputed in cleaning using the median for routes of the same difficulty tier, with the imputation logged |
| is_featured | boolean | [Core] `routes_app.Route.is_featured` | |
| active | boolean | [Core] `routes_app.Route.active` | ~5% of routes marked inactive, simulating retired routes over the 7-year window |
| trailhead_lat / trailhead_lon | decimal | [Ext] | Approximate real-world trailhead coordinates for the named route (e.g. Llanberis for Snowdon via Llanberis Path), added for map visuals — not survey-grade precision, but genuinely placed at the right mountain/valley, not randomly generated. Validated against a UK bounding box (lat 49.5-61.0, lon -8.5-2.0) during cleaning |

Fifty-three routes are seeded across seven regions. Thirty are originally synthetic (seeded before real fixture data was available); the remaining 27 are pulled directly from `backend/fixtures/routes.json` in the live UK Summit Guides repo — real route names, difficulty, distance, elevation, and exact trailhead coordinates (`map_center_lat`/`map_center_lng` in the fixture), not approximated. The live app groups these into 5 regions (Scotland, Lake District, Wales, Peak District, Yorkshire Dales); rather than restructure the existing 6 synthetic regions to match, each real route was mapped to whichever of the 6 it's actually located in (e.g. a "Wales"-region route near Snowdon maps to "Snowdonia" here), and **Yorkshire Dales was added as a 7th region** specifically because one real route (Ingleborough) didn't fit any of the original 6 — a genuine addition, not a restructure. Four routes that existed in both the synthetic seed and the real fixture under slightly different names (e.g. "Ben Nevis via CMD Arete" vs. the real "Ben Nevis via CMD Arête") were upgraded to the real data in place rather than kept as near-duplicate entries.

**Difficulty affects more than pricing.** Route difficulty also influences two other generated fields, on purpose: review ratings run measurably lower for harder routes (`config.DIFFICULTY_RATING_ADJUSTMENT` — moderate +0.20, hard +0, advanced -0.35, layered on top of the existing season effect), and ops/weather cancellation rate scales from 4% (moderate) to 10% (advanced) rather than being flat across all difficulty tiers (`config.DIFFICULTY_OPS_CANCEL_RATE`). Earlier versions of this dataset had difficulty affect price but nothing else, which produced a flat, uninteresting relationship between difficulty and satisfaction/cancellations on the Route dashboard — this was corrected once that flatness showed up as a real finding while building the dashboard, not designed in from the start.

## ScheduledTour

| Field | Type | Provenance | Notes / cleaning rule |
|---|---|---|---|
| tour_id | int | generated surrogate key | |
| route | FK → Route | [Core] `bookings.ScheduledTour.route` | |
| guide | FK → Guide, nullable | [Core] `bookings.ScheduledTour.guide` | ~2% of tours have no guide assigned (nobody from the relevant region was available) — left null, not imputed |
| date | date | [Core] `bookings.ScheduledTour.date` | Spans 2019-01-01 to 2025-12-31; includes a deliberate 2020 volume dip reflecting COVID-19 disruption |
| season | string (`winter`/`summer`) | [Core] `bookings.ScheduledTour.season` | Closed enum, matches real app |
| start_time | time | [Core] `bookings.ScheduledTour.start_time` | |
| price_pp | decimal | [Core] `bookings.ScheduledTour.price_pp` | Modelled from difficulty, duration, and year-on-year inflation; ~2% stored as messy currency strings in raw |
| max_group_size | int | [Core] `bookings.ScheduledTour.max_group_size` | 3 by default; some advanced routes capped at 2 for safety |
| status | string (`draft`/`open`/`full`/`cancelled`) | [Core] `bookings.ScheduledTour.status` | Derived *after* bookings are generated: `full` if booked spaces reach capacity, `cancelled` if flagged for ops/weather reasons (4-10% of tours, scaling with difficulty — advanced routes run in more exposed terrain and are cancelled more often) or if a published tour attracted zero bookings (70% of those are treated as cancelled, matching how a small operator would pull an empty tour), otherwise `open` |

**Known simplification:** guide availability is modelled via company join/leave dates so a guide never appears on a tour before joining or after leaving — but route retirement (`Route.active`) is not similarly date-gated, since the real schema doesn't timestamp when a route was retired.

## Booking

| Field | Type | Provenance | Notes / cleaning rule |
|---|---|---|---|
| booking_id | int | generated surrogate key | |
| scheduled_tour | FK → ScheduledTour | [Core] `bookings.Booking.scheduled_tour` | |
| booking_reference | string | [Core] `bookings.Booking.booking_reference` | Matches the real app's format: 10-char uppercase hex |
| party_size | int (1–3) | [Core] `bookings.Booking.party_size` | Sum of party sizes per tour never exceeds `max_group_size` |
| contact_name | string | [Core] `bookings.Booking.contact_name` | Casing inconsistencies injected |
| contact_email | string | [Core] `bookings.Booking.contact_email` | ~3% malformed (missing `@`) |
| contact_phone | string | [Core] `bookings.Booking.contact_phone` | UK-format synthetic numbers |
| emergency_contact | string, nullable | [Core] `bookings.Booking.emergency_contact` | `blank=True` in the real model — ~30% null here to match |
| notes | string, nullable | [Core] `bookings.Booking.notes` | `blank=True` — ~90% null |
| status | string (`pending`/`confirmed`/`cancelled`/`amended`) | [Core] `bookings.Booking.status` | `pending` only appears for bookings created in the final two weeks of the dataset window, matching how a real "as of" extract would look |
| list_price | decimal | [Ext] | Undiscounted price: `price_pp × party_size`. Doesn't exist as a separate field in the real app (which only stores the final `total_price`) — added specifically to support discount analysis, since you can't measure a discount without knowing what the price would have been without it |
| discount_pct | decimal (0-0.30) | [Ext] | 0 for the ~87% of bookings with no discount. When a discount applies, correlated with the assigned guide's `discount_tendency_pct` (see Guide) — not applied at all for unguided tours |
| discount_applied | boolean | [Ext] | Whether any discount was applied to this booking |
| total_price | decimal | [Core] `bookings.Booking.total_price` | The actual price paid: `list_price × (1 − discount_pct)`. ~2% of `list_price`/`total_price` stored as messy currency strings independently — occasionally this causes a small (~£1) inconsistency between the stored `total_price` and `list_price × (1 − discount_pct)` when one of the two got whole-pound-rounded in raw data and the other didn't. This is intentional messiness, not a generation bug — the cleaning pipeline flags it via the `total_price_discount_mismatch` metric rather than silently correcting it |
| archived_at | datetime, nullable | [Core] `bookings.Booking.archived_at` | Set for ~50% of cancelled bookings older than 12 months, simulating periodic archiving |
| created_at | datetime | [Core] `bookings.Booking.created_at` | Booking lead time is log-normally distributed (median ~25 days ahead, long tail out to 400 days) |

## Payment

| Field | Type | Provenance | Notes / cleaning rule |
|---|---|---|---|
| payment_id | int | generated surrogate key | |
| booking | FK → Booking (1:1) | [Core] `payments.Payment.booking` | |
| stripe_payment_intent_id / stripe_checkout_session_id / stripe_refund_id | string | [Core] `payments.Payment` | Synthetic Stripe-shaped IDs, not real |
| amount | decimal | [Core] `payments.Payment.amount` | Mirrors the booking's `total_price` |
| currency | string | [Core] `payments.Payment.currency` | Always GBP in substance; ~25% stored as lowercase `gbp` in raw to simulate inconsistent casing |
| status | string (`pending`/`paid`/`refund_pending`/`refunded`/`failed`) | [Core] `payments.Payment.status` | Derived from the linked booking's status |
| paid_at / refunded_at | datetime, nullable | [Core] `payments.Payment` | Populated only when status is `paid` / `refunded` respectively |

## Review [Ext]

| Field | Type | Notes / cleaning rule |
|---|---|---|
| booking_id | int | FK → Booking. Only ~45% of confirmed/amended bookings have a review — this is the response rate, not every completed trip is reviewed |
| overall_rating / guide_rating / route_rating / safety_rating / value_rating | int (1–5) | Overall skews slightly lower for winter tours; the other four ratings are generated correlated to overall rather than independently, since real reviewers rarely give wildly inconsistent sub-scores. ~2–3% missing per field, and cleaning **leaves these null rather than imputing** — guessing a satisfaction score is worse than admitting it's unknown |
| comment_length | int | Word count proxy; longer for 1–2★ and 5★ reviews (people write more when they feel strongly), shorter for 3★ |
| would_recommend | boolean | Correlated with overall_rating (≥4★ → yes, with ~8% noise); cleaning parses the raw yes/no text (in mixed casing) to a real boolean |

## Weather [Ext]

| Field | Type | Notes / cleaning rule |
|---|---|---|
| date, region | date, FK → Region | Daily grain, every region, full 2019–2025 window |
| temperature_c | decimal | Seasonal curve per region's climate profile, with daily noise |
| rain_mm | decimal | Gamma-distributed, heavier in winter months |
| wind_speed_kmh | decimal | Higher in winter and in stormier regions (Scottish Highlands, Cairngorms) |
| visibility_km | decimal | Inversely related to rainfall |
| snow_depth_cm | decimal | Only non-zero in winter months when temperature drops below ~3°C |
| storm_warning | boolean | Probability scaled by region storm-proneness and season |

**Known modelling choice:** weather is generated independently of the ScheduledTour cancellation flag rather than causally driving it — the "weather-related cancellation %" KPI is computed by *joining* cancelled tours to same-date/region storm-warning or high-rain days at the SQL/DAX layer. This mirrors how the business would actually attribute cancellations after the fact, and is documented here so the methodology is transparent rather than implied as a hard-coded causal simulation.

## Marketing [Ext] + Booking Attribution [Ext]

| Field | Type | Notes / cleaning rule |
|---|---|---|
| booking_id → channel | FK, string | A separate small table (not a column on Booking) so the Core Booking table stays untouched. Channel mix shifts gradually over the years (paid_social share grows, organic share shrinks slightly) |
| campaign, channel, year_month | string | Campaign/channel/month grain |
| spend | decimal | Zero for organic/direct/referral (word-of-mouth/SEO/repeat traffic — no media cost); driven by conversions × channel CPA for paid channels |
| clicks, impressions | int | Derived from conversions using channel-specific conversion rate and CTR assumptions |
| conversions | int | **Reconciles exactly with confirmed/amended bookings**, not every attributed booking. A cancelled or still-pending booking gets attributed to a channel (for channel-mix reporting elsewhere) but never counts as a marketing conversion, since it never actually converted. *(Corrected — an earlier version counted every attributed booking regardless of status, which inflated both conversions and revenue; caught when Marketing Revenue was found to exceed total confirmed company revenue while building the Marketing dashboard.)* |
| revenue | decimal | Sum of `total_price` for **confirmed/amended** bookings attributed to that channel/month — matches total confirmed revenue to within rounding (see note above) |

## WebsiteAnalytics [Ext]

| Field | Type | Notes / cleaning rule |
|---|---|---|
| week_starting, traffic_source, device | date, string, string | Weekly grain (daily would over-model a small operator's traffic); traffic sources mirror the Marketing channel list for consistency |
| sessions, users | int | Seasonal (summer/December uplift), source- and device-weighted |
| bounce_rate, conversion_rate | decimal (0–1) | Mobile bounce rate modelled higher than desktop; conversion rate centred on each channel's assumed rate |
| browser | string | Weighted categorical (Chrome/Safari/Edge/Firefox/Other) |
| country | string | ~84% United Kingdom; remainder a small set of countries, with the same country-name inconsistency helper used elsewhere (`UK` / `U.K.` / `United Kingdom` variants). Cleaning maps all recognised variants to one canonical form via `canonicalise_country()`, and the quality log records only the genuine corrections (not rows that were already canonical) |

## EquipmentHire [Ext]

| Field | Type | Notes / cleaning rule |
|---|---|---|
| booking_id | int | FK → Booking. Only generated for confirmed/amended bookings (~40% hire rate among those) |
| boots / waterproofs / poles / helmet / ice_axe / crampons | boolean | Ice axe and crampon hire probability roughly 2.5× higher for winter + hard/advanced-difficulty bookings, reflecting real equipment needs |
| hire_revenue | decimal | Sum of item price × quantity hired (quantity capped at the booking's party size) |

## DimDate [derived, warehouse-only]

Unlike every other table above, `DimDate` isn't built from a raw/cleaned CSV — it's generated directly in `src/warehouse/build_warehouse.py`, one row per calendar day across the dataset's full date range. A few fields are worth documenting since they encode real business logic, not just calendar arithmetic:

| Field | Type | Notes |
|---|---|---|
| week_start_date / week_end_date | date | **Retail week**: Sunday → Saturday, not the ISO standard (Monday → Sunday). Computed as the most recent Sunday on/before each date |
| week_number | int (1-53) | Resets each `retail_year`. Simplification: a week "belongs" to the calendar year of its Sunday (`week_start_date`), not a majority-of-days rule some retail calendars use — documented here rather than silently assumed |
| retail_year | int | The year `week_number` resets against — see above |
| is_bank_holiday | boolean | England & Wales bank holidays, computed by `src/utils/uk_calendar.py` (Good Friday/Easter Monday via `dateutil.easter`, fixed-date holidays with real UK weekend-substitution rules, e.g. Christmas Day on a Saturday moves to the following Monday). Scotland's holidays differ slightly (e.g. St Andrew's Day) — using the E&W calendar UK-wide is a documented simplification, not an oversight |
| is_summer_holiday | boolean | Approximates the English school summer holiday window (20 July – 31 August, every year). Real dates vary by 1-2 weeks by region/year — a fixed window was judged not worth the added complexity here |

**These flags actively shape the data, not just describe it.** `src/generation/generate_transactions.py` weights which dates get scheduled tours using exactly this logic (weekend × bank holiday × summer holiday multipliers, compounding) — bank holidays run at roughly **2.9× regular weekday revenue**, weekends at **2.2×**. The flags on `DimDate` let that pattern actually be *seen* in Power BI, not just exist invisibly in the generation code.

---

All extension-layer generation and cleaning are complete. Dimensional model design (star schema) is next.