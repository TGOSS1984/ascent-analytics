# Real-World Lessons: Power BI Schema Fragility

Every other layer of this project — Python generation, cleaning, the SQL warehouse — is version-controlled, code-reviewable, and reproducible from source. The Power BI semantic model isn't, and this document is an honest account of what that cost in practice, why it happens, and how it was eventually handled systematically rather than improvised each time.

## The core problem

Power BI's Import mode captures a table's schema — its columns, their inferred types — at the point a query is first connected, as a fixed sequence of Power Query steps (typically ending in a "Changed Type" step that explicitly lists every known column). A plain **Refresh** re-runs those steps against the current source file, but it doesn't re-detect the source's column *set* — if a CSV gains a new column, Refresh happily re-imports all the columns it already knew about and silently ignores the new one, because nothing in the existing query asks for it.

The only reliable fix is to **delete the table and reimport it fresh**, which forces Power BI to build a new query from scratch against the file's current columns. That sounds like a minor inconvenience. It isn't — because deleting a table deletes *everything that was homed on it*:

- Every relationship touching that table
- Every calculated column that lived on it
- Every hierarchy built from its fields
- Column-level settings (Sort by Column, "Mark as date table")
- **Every DAX measure whose Home table was that table** — regardless of what the measure's formula actually references

That last point is the expensive one, and it's easy to underestimate until it happens: measures don't need to reference their home table's own columns, so it's natural to end up with dozens of measures homed on one convenient table (in this project, `FactBookings`) purely out of habit, not because they logically belong there.

## What this actually cost, with real numbers

Partway through this project, `DimDate` needed new columns (retail week fields, UK bank holiday flags), `DimGuide` needed a new discount-tendency field, and `FactBookings` needed new discount fields — three tables, driven by one feature addition. Reimporting all three (plus `DimRoute`, which had grown from 30 to 53 rows) triggered a full model rebuild:

- **17 relationships** rebuilt from scratch, including re-diagnosing which ones needed to stay *inactive* to avoid ambiguous-path errors (a distinct problem in its own right — see `docs/architecture/README.md`'s "Deliberate modelling decisions" section)
- **3 calculated columns** (`Region Name`, `Lead Time Bucket`, `Experience Band`)
- **2 hierarchies** (the Date calendar hierarchy, the Region → Route drill-down) plus 2 Sort by Column settings
- **29 DAX measures**, rebuilt in 8 batches, because `FactBookings` had quietly become the home table for almost every measure in the report — base revenue/booking metrics, guide utilisation, customer repeat rate, time-intelligence (PY/YTD/growth), route "winner" measures, and the newer discount-analysis measures, all lost in one deletion

None of that data was actually at risk — it all lived safely in the underlying CSVs and SQL warehouse the whole time. What was lost was the *presentation-layer wiring* connecting that data to a working report, and rebuilding it correctly, in the right dependency order (relationships before calculated columns before hierarchies before measures), took real, deliberate effort.

## Handling it systematically

The second time this happened, it was treated as a proper engineering problem rather than something to muddle through from memory: [`docs/POWERBI_REBUILD_CHECKLIST.md`](POWERBI_REBUILD_CHECKLIST.md) is an ordered, dependency-aware checklist built specifically so a full reimport never has to be improvised again — covering not just what to rebuild, but what to verify *didn't* need rebuilding (measures on untouched tables), and a page-by-page final check for anything still broken.

Two related gotchas surfaced during this same debugging arc, worth naming since they're easy to mistake for something else:

- **Autodetect isn't trustworthy after a reimport.** Power BI's relationship Autodetect proposed an active `DimGuide → DimRegion` relationship that conflicted with an existing active path through `DimRoute`, producing no visible error until a *different* relationship was manually attempted and Power BI's ambiguous-path check caught the conflict. Autodetect optimises for "a plausible-looking model," not for the specific active/inactive choices a report's measures actually depend on.
- **Column data types don't always survive a reimport either.** Boolean flags (`is_bank_holiday`, `discount_applied`) occasionally came back as Whole Number instead of True/False after a fresh import, breaking any DAX comparing them against `TRUE()`/`FALSE()` — a separate, subtler failure mode from the "table needs reimporting" problem, since the symptom (a comparison-type error) doesn't obviously point back to a reimport at all.

## The broader, honest lesson

This is a real, structural limitation of building analytics on a desktop BI tool rather than a fully code-defined semantic layer: the Python and SQL layers of this project can be diffed, reviewed, and rolled back with `git`; the Power BI layer, as built here, can't be. A `.pbix` file is a binary blob — useful to open and use, useless to code-review.

The more mature version of this setup would define the semantic model in a text format that *can* be version-controlled — **Tabular Editor with TMDL (Tabular Model Definition Language)** is the standard tool for this in the Power BI ecosystem, letting measures, relationships, and table structures live as reviewable `.tmdl` files alongside the Python and SQL in this same repo, rather than trapped inside a binary file. That's a deliberate, named next step for this project, not something quietly worked around — see the main README's roadmap.