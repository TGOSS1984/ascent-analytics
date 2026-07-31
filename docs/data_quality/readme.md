# Data Quality Log

`core_pipeline_log.csv` in this folder is the output of `src/cleaning/run_pipeline.py`'s `QualityLog` — a real, generated record of what the cleaning pipeline actually did on its most recent run, not a static claim. It's regenerated every time the pipeline runs, so it always reflects the current dataset.

## Format

| Column | Meaning |
|---|---|
| run_started_at | UTC timestamp of the pipeline run that produced this row |
| table | Which entity the row is about (Region, Guide, Route, ScheduledTour, Booking, Payment — extension entities are added in the next pipeline stage) |
| metric | One of: `row_count`, `completeness`, `duplicates_removed`, `validation_failures`, or a table-specific metric (e.g. `elevation_gain_imputed`, `malformed_emails_repaired`, `currency_casing_fixed`) |
| stage | For `row_count` rows: `raw` or `cleaned`. Otherwise `cleaning`. |
| value | The metric's value |
| notes | Free-text explanation of the rule applied, where relevant |

## How this feeds the Data Quality Dashboard

The KPI catalogue (`docs/kpi_catalogue/README.md`, section 9) defines Completeness %, Duplicate Rate, Validation Failure Rate, and Row Counts by Stage — all sourced directly from this log rather than being separately calculated in Power BI. The idea is that data quality reporting should be a by-product of the pipeline actually running, not a manually-maintained claim bolted on afterwards.

## Reading a sample run

As of the core-entities cleaning stage, a typical run shows:
- Zero validation failures across all six core tables
- Zero orphaned foreign keys
- ~855 malformed emails automatically repaired (the `" at "` → `"@"` corruption pattern)
- ~7,000 payment records with lowercase `gbp` currency casing standardised to `GBP`
- 1 route's missing elevation gain imputed from the median for its difficulty tier
- 1 guide's missing qualifications left as a genuine gap (flagged, not guessed)

Exact figures vary run-to-run only if the generation scripts are re-run with different parameters — the generation itself is seeded, so a clean re-run of the whole pipeline should reproduce the same numbers.