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

---

_To be extended next: ScheduledTour, Booking, Payment (Core), followed by Review, Weather, Marketing, WebsiteAnalytics, EquipmentHire (Extensions)._