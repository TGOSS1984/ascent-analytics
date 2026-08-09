# From Portfolio Project to Production

Everything in this repo is built to be **credible, not deployed** — a synthetic dataset, a SQLite file, a pipeline you run by hand. That was the right call for a portfolio project (see `readme.md`'s "credibility over scale" note), but it's worth being explicit about what would actually need to change if [UK Summit Guides](https://github.com/TGOSS1984/uk-summit-guides) were a real, live business asking for this warehouse to run against its real bookings. This doc is that narrative, in four parts.

## 1. SQLite → Postgres

**Why SQLite was right here:** it's a single file, needs no server, and the whole warehouse — 12 tables, ~300K cleaned+raw rows — fits comfortably in it. Anyone can clone the repo, run `python run_pipeline.py`, and get a `warehouse.db` file with zero setup. That's exactly the right trade for a project meant to be cloned and inspected.

**What would force a move to Postgres:**

- **Concurrent writes.** SQLite locks the whole database file for a write; that's invisible for a batch pipeline that runs once and stops, but breaks the moment more than one process needs to write at the same time — e.g., the pipeline running a refresh while someone's also running ad-hoc analysis queries against the same file.
- **UK Summit Guides already runs on Postgres.** The live app is React + Django REST Framework + PostgreSQL — so a real warehouse wouldn't be migrating *to* Postgres so much as connecting *directly* to the same database family the source system already uses, likely via **logical replication or a read replica** rather than a nightly file export, so the warehouse never contends with production traffic for locks.
- **Power BI Service needs a live connection, not a laptop file.** A `.pbix`/`.pbip` pointed at `warehouse.db` only refreshes when someone's machine has that file on disk. Publishing to the Power BI Service for real use requires either a **gateway** (an on-prem/VM process that can reach the database and bridge it to the cloud service) or a cloud-native database Power BI can query directly — SQLite qualifies for neither.
- **Scale, eventually.** At ~30,000 bookings over 7 years this project deliberately stays small (see `readme.md` — "groups capped at 3 people" keeps volume realistic for the business, not inflated for effect). A real, growing business would outgrow SQLite's single-writer model well before the row count itself became the bottleneck.

**What stays the same:** the star schema itself (`sql/schema/`), the Kimball-style fact/dimension split documented in `docs/architecture/readme.md`, and the DAX measures in `powerbi/dax_measures.md` — none of that is SQLite-specific. Postgres is a drop-in for *where* the tables live, not a redesign of *what* they look like. The main code change would be in `src/warehouse/build_warehouse.py` and `export_for_powerbi.py`, which currently talk to SQLite directly (`sqlite3` / a SQLite-flavoured connection string) and would need to move to a Postgres driver (`psycopg2`/`asyncpg`) behind the same interface.

## 2. Scheduled refresh

**What happens today:** `run_pipeline.py` runs all 8 pipeline steps — generate, clean, validate, load, export — in one shot, by hand, on demand. There's no schedule, no failure alerting, no incremental logic; every run rebuilds the warehouse from scratch.

**What real scheduled refresh needs:**

- **A trigger, not a person.** Power BI Service supports scheduled refresh natively (up to 8x/day on shared capacity, more on Premium/Fabric capacity) against a registered data source — but that only refreshes the semantic model *from* the warehouse. Something still has to run the pipeline itself on a schedule to keep the warehouse current: a cron job, a GitHub Actions scheduled workflow (the repo already has CI infrastructure from gap 1 that a scheduled job could extend), or an orchestrator like Airflow/Dagster if the pipeline grows more steps or dependencies.
- **Incremental, not full-rebuild.** The current pipeline is a full rebuild every time, which is fine at ~30K bookings but wouldn't stay fine at real production volume over years of history. A production version would need each pipeline step to support "only process what's new since the last run" — new bookings, new payments — rather than regenerating and re-validating everything.
- **Failure needs to be loud.** Right now, if a pipeline step fails, the person who ran it by hand sees it in their terminal immediately. On a schedule, nobody's watching — a failed run needs to page or notify someone (Slack webhook, email, PagerDuty), and ideally leave the warehouse in its last-known-good state rather than half-updated.
- **The pandera schema validation already in `src/cleaning/schemas.py` becomes the safety net here** — it's already designed to catch bad data before it lands in the warehouse; on a schedule, that's the thing standing between "a malformed upstream export" and "a broken dashboard nobody notices until a stakeholder asks about it."

## 3. Row-Level Security (RLS)

This one has a natural fit with the model as already built. `DimRegion` sits at the center of the star schema (`DimRoute → DimRegion`, `DimGuide → DimRegion` [inactive, see `docs/architecture/readme.md`], `FactWeather → DimRegion`) — which means **region is already the natural boundary for who should see what.**

**The scenario:** imagine UK Summit Guides grows regional managers — someone responsible for Snowdonia operations shouldn't necessarily see Scottish Highlands revenue and vice versa, but both need the same Executive/Sales/Route dashboards, scoped to their own patch.

**How Power BI RLS would apply here:**

- Define **roles** in the semantic model (Power BI Desktop → Modeling → Manage Roles), one per region or a general "Regional Manager" role parameterised by the viewer's identity.
- Each role gets a **DAX filter expression** on `DimRegion`, something like:
  ```
  [name] = USERPRINCIPALNAME()
  ```
  more realistically resolved through a small **mapping table** (email → allowed region(s)), since a manager's email address isn't literally the region name — RLS filters typically join through a bridge table like `DimRegionAccess(user_email, region_name)` rather than comparing identity directly against a business key.
- Because `DimRegion` already propagates through the active relationship chain (`DimRoute → DimRegion`, and `FactBookings` reaches it via `DimRoute` per the documented inactive-relationship decision), **a filter on `DimRegion` alone would correctly restrict `FactBookings`, `FactReviews`, `FactEquipmentHire`, and `FactWeather` simultaneously** — the star schema's existing relationship design is what makes this cheap to add later rather than a redesign.
- **The gap:** `DimCustomer` isn't region-scoped (a customer books across regions in principle), and `FactMarketing`/`FactWebsiteAnalytics` aren't region-scoped at all — they're channel/week grain, not tied to `DimRegion`. A real RLS rollout would need an explicit decision about whether those tables stay globally visible to every regional manager or get excluded from their view entirely, since the model as built doesn't currently give them a region-shaped handle to filter on.
- **Testing RLS is easy to skip and shouldn't be** — Power BI Desktop's "View As Roles" lets you preview exactly what a Snowdonia manager would see before publishing, and it's worth doing per-role, not just once, since a role definition that looks right in the DAX can still leak data through an un-scoped visual or a table RLS doesn't reach.

## 4. A real ingestion API

**What generates the data today:** `src/generation/` uses Faker plus deliberately-injected messiness (`docs/data_quality/`) to produce realistic-but-synthetic CSVs, which `src/cleaning/` then cleans and validates before loading into the warehouse. There is no real ingestion — it's a data *simulator*, honestly labelled as such throughout the project.

**What a real source looks like:** it's not hypothetical — [UK Summit Guides](https://github.com/TGOSS1984/uk-summit-guides) is a real Django REST Framework app with real models (`Region`, `Guide`, `Route`, `ScheduledTour`, `Booking`, `Payment`) that this warehouse's core dimensions and facts are already aligned to field-for-field (see `readme.md`'s "Relationship to UK Summit Guides" section). The natural production path is:

- **Direct database access**, if warehouse and app share infrastructure — a read replica of the app's Postgres database, queried on a schedule, no API involved. Simplest option, and viable precisely because both projects already agree on schema.
- **A REST pull**, if the warehouse needs to stay decoupled from the app's database — Django REST Framework can expose the same models the warehouse already mirrors (`/api/bookings/?updated_since=...`), and the pipeline's ingestion step polls incrementally rather than bulk-exporting everything each run.
- **Event-driven**, for the more ambitious version — the Django app publishes a `booking.created` / `payment.confirmed` event (webhook, or a message queue like Celery-with-Redis, which fits naturally next to a Django stack) and the warehouse ingests near-real-time instead of batch. Overkill for a small guiding operation's actual needs, but worth naming as the ceiling of what's possible.

**What wouldn't carry over cleanly:** the synthetic extensions — `FactWeather`, `FactMarketing`, `FactWebsiteAnalytics`, `FactEquipmentHire`, and `DimGuide.discount_tendency_pct` — have **no equivalent in the real UK Summit Guides schema** (this is called out explicitly in `readme.md` and the data dictionary as deliberate scope extension, not oversight). A real ingestion pipeline would need genuinely separate integrations for each: a weather API (e.g. Met Office DataPoint) keyed on region + date, a marketing platform's own reporting API (Google Ads, Meta) rather than a single unified table, and website analytics from whatever's actually instrumented (GA4, Plausible) rather than assumed. None of that is a warehouse-design problem — it's four separate "does this data source exist in the real business yet" problems, and the honest answer for a small guiding operation today is probably "not yet, and maybe not worth building until the core booking pipeline is real."

## Summary

None of the four sit as a checklist item literally waiting to be built — this project's value was always in the analysis and the modelling discipline, not in operating a real production system. But being explicit about the gap between "demonstrates the right patterns" and "would survive contact with a real, growing, multi-user business" is itself part of doing this credibly: a warehouse designed with `DimRegion` as a first-class dimension, source tables aligned field-for-field to a real running app, and validation baked into the cleaning step isn't an accident — those choices are exactly what make the four extensions above additions to the existing design rather than rewrites of it.