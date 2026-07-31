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

Thirty routes are seeded across the six regions, using real UK mountain routes as the naming basis (e.g. Snowdon via Llanberis Path, Ben Nevis via CMD Arete, Helvellyn via Striding Edge) so route-level analysis reads as credible rather than placeholder data.

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
| status | string (`draft`/`open`/`full`/`cancelled`) | [Core] `bookings.ScheduledTour.status` | Derived *after* bookings are generated: `full` if booked spaces reach capacity, `cancelled` if flagged for ops/weather reasons (~6% of tours) or if a published tour attracted zero bookings (70% of those are treated as cancelled, matching how a small operator would pull an empty tour), otherwise `open` |

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
| total_price | decimal | [Core] `bookings.Booking.total_price` | `price_pp × party_size`; ~2% stored as messy currency strings |
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

---

_To be extended next: Review, Weather, Marketing, WebsiteAnalytics, EquipmentHire (all synthetic Extensions)._