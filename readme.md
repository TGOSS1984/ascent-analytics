# ⛰️ Ascent Analytics

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)]()
[![SQL](https://img.shields.io/badge/SQL-SQLite%20%7C%20Postgres-4479A1?style=for-the-badge&logo=postgresql&logoColor=white)]()
[![Power BI](https://img.shields.io/badge/BI-Power%20BI-F2C811?style=for-the-badge&logo=powerbi&logoColor=black)]()
[![Pandas](https://img.shields.io/badge/Data-Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white)]()
[![Status](https://img.shields.io/badge/Status-In%20Development-orange?style=for-the-badge)]()

> The analytics companion to **[UK Summit Guides](https://github.com/TGOSS1984/uk-summit-guides)** — a full end-to-end BI platform that takes raw, messy operational data and turns it into a governed warehouse, a documented KPI catalogue, and an executive-ready Power BI reporting suite.

---

## 📚 Table of Contents

- [📖 Overview](#-overview)
- [🎯 Business Problem & KPIs](docs/business_problem.md)
- [🔗 Relationship to UK Summit Guides](#-relationship-to-uk-summit-guides)
- [🧱 Data Model](#-data-model)
- [🏗️ Architecture](#️-architecture)
- [🛠️ Tech Stack](#️-tech-stack)
- [📂 Project Structure](#-project-structure)
- [🧹 Data Cleaning](#-data-cleaning)
- [🗃️ SQL Warehouse](#️-sql-warehouse)
- [📊 KPIs & Dashboards](#-kpis--dashboards)
- [🔍 Data Quality](#-data-quality)
- [⚙️ Local Setup](#️-local-setup)
- [🗺️ Roadmap](#️-roadmap)
- [📌 Notes on Realism & Scope](#-notes-on-realism--scope)

---

## 📖 Overview

**Ascent Analytics** is a self-contained Business Intelligence project built around a synthetic but realistic dataset for a small UK-based guided mountain tour operator. It exists to demonstrate the full analytics lifecycle a data analyst is expected to own:

`Raw data → Python cleaning → SQL warehouse (star schema) → Power BI semantic model → Executive dashboards → Written insight & recommendations`

Rather than starting from a dashboard, this project starts from the same place a real analyst would: messy, imperfect operational data that needs to be understood, validated, cleaned, modelled, and only then visualised.

## 🔗 Relationship to UK Summit Guides

[UK Summit Guides](https://github.com/TGOSS1984/uk-summit-guides) is a live full-stack booking platform (React + Django REST Framework + PostgreSQL) for a small guided mountain tour company. Ascent Analytics is designed as its data/BI counterpart:

- **Core entities are aligned 1:1** with the real Django models (`Region`, `Guide`, `Route`, `ScheduledTour`, `Booking`, `Payment`) — same field names, same business rules (e.g. max party size of 3, difficulty levels of `moderate`/`hard`/`advanced`, seasons of `winter`/`summer` only).
- **Extended entities** (`Weather`, `Marketing`, `WebsiteAnalytics`, `EquipmentHire`, `Review`) do **not** exist in the live application. They're generated synthetically to demonstrate warehouse modelling and KPI work across a fuller commercial data estate. This is documented explicitly — see [Notes on Realism & Scope](#-notes-on-realism--scope) — rather than implied as real production data.

## 🧱 Data Model

_Full data dictionary lives in [`docs/data_dictionary/`](docs/data_dictionary/) — filled in as each entity is built._

| Entity | Source of truth | Status |
|---|---|---|
| Region | Aligned to `routes_app.Region` | 🔲 Not yet built |
| Guide | Aligned to `routes_app.Guide` | 🔲 Not yet built |
| Route | Aligned to `routes_app.Route` | 🔲 Not yet built |
| ScheduledTour | Aligned to `bookings.ScheduledTour` | 🔲 Not yet built |
| Booking | Aligned to `bookings.Booking` | 🔲 Not yet built |
| Payment | Aligned to `payments.Payment` | 🔲 Not yet built |
| Review | Synthetic extension | 🔲 Not yet built |
| Weather | Synthetic extension | 🔲 Not yet built |
| Marketing | Synthetic extension | 🔲 Not yet built |
| WebsiteAnalytics | Synthetic extension | 🔲 Not yet built |
| EquipmentHire | Synthetic extension | 🔲 Not yet built |

## 🏗️ Architecture

```
Raw Data (CSV, synthetic + intentionally messy)
        │
        ▼
Python Cleaning & Validation  (src/cleaning)
        │
        ▼
SQL Warehouse — Star Schema  (sql/schema)
        │
        ▼
Power BI Semantic Model + DAX  (powerbi/)
        │
        ▼
Executive & Departmental Dashboards
        │
        ▼
Insight Report & Recommendations  (docs/)
```

## 🛠️ Tech Stack

- **Python** — pandas, NumPy, Faker (synthetic data), pandera (validation)
- **SQL** — SQLite for development, with Postgres-compatible DDL for production
- **Power BI** — DAX measures, star-schema semantic model
- **Git/GitHub** — incremental, documented commit history
- **Markdown** — architecture docs, data dictionary, KPI catalogue

## 📂 Project Structure

```
ascent-analytics/
├── data/
│   ├── raw/            # Generated "messy" source data
│   ├── cleaned/         # Post-cleaning outputs
│   └── warehouse/       # SQLite warehouse database
├── src/
│   ├── generation/      # Synthetic data generation scripts
│   ├── cleaning/        # Cleaning & validation pipeline
│   └── utils/           # Shared helpers
├── sql/
│   ├── schema/          # DDL for fact/dimension tables
│   ├── views/            # Reporting views
│   ├── procedures/       # Stored procedures
│   └── queries/           # Analytical query library
├── notebooks/            # Exploratory analysis
├── powerbi/               # .pbix file + screenshots
├── docs/
│   ├── architecture/      # Architecture diagrams
│   ├── data_dictionary/   # Field-level documentation
│   ├── kpi_catalogue/      # KPI definitions & formulas
│   └── data_quality/       # Data quality scorecards
└── tests/                  # Pipeline tests
```

## 🧹 Data Cleaning

The Python cleaning pipeline (`src/cleaning/`) turns the deliberately messy raw CSVs into validated, warehouse-ready tables. It's split into two stages tracked separately on the roadmap:

- **Core entities** (this stage — `run_pipeline.py`): Region, Guide, Route, ScheduledTour, Booking, Payment
- **Extension entities** (next stage): Review, Weather, Marketing, WebsiteAnalytics, EquipmentHire

Run it (after all three generation scripts):

```bash
python -m src.cleaning.run_pipeline
```

What it does, per table:

- **Deduplication** — exact-duplicate rows (simulating double form submissions) are dropped and counted
- **Text normalisation** — inconsistent casing/whitespace in names, regions, and route names standardised to title case; closed-enum fields (status, difficulty, season, currency) standardised to lowercase/uppercase as appropriate
- **Currency parsing** — values stored as `"£99.95"`, `"GBP 99.95"`, or `"£1,133.78"` all parse to a clean float
- **Email repair** — the one known corruption pattern (`@` replaced with `" at "`) is repaired automatically; anything else that still doesn't look like a valid email is flagged via `contact_email_invalid` rather than guessed at
- **Missing-value handling** — some gaps are left as genuine gaps (e.g. a guide's missing qualifications, since inventing a qualification would be worse than admitting it's unknown); others are imputed with a documented, auditable rule (e.g. missing route elevation filled with the median for that difficulty tier) — see `docs/data_dictionary/README.md` for which rule applies to which field
- **Referential integrity checks** — every foreign key is checked against its parent table, with any orphans logged rather than silently dropped
- **Schema validation** — every cleaned table is validated against a [pandera](https://pandera.readthedocs.io/) schema (`src/cleaning/schemas.py`) enforcing types, ranges, and closed-enum values before it's written out

Every rule fires into a `QualityLog`, written to [`docs/data_quality/core_pipeline_log.csv`](docs/data_quality/core_pipeline_log.csv) — row counts by stage, duplicates removed, values imputed/repaired, and validation failure counts. This is the same log data the Data Quality Dashboard will visualise.

## 🗃️ SQL Warehouse

_To be documented as the star schema is built._

## 📊 KPIs & Dashboards

_To be documented as dashboards are built._

## 🔍 Data Quality

_To be documented alongside the data quality dashboard._

## ⚙️ Local Setup

```bash
git clone <repo-url>
cd ascent-analytics
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

Notebooks (`notebooks/`) need an extra, optional install — kept separate because `jupyter` pulls in `jupyterlab`'s large, deeply-nested asset tree, which can hit Windows' path-length limit (especially inside a OneDrive-synced folder):

```bash
pip install -r requirements-notebook.txt
```

If that fails on Windows with an `OSError` about a missing nested file path, see the comment at the top of `requirements-notebook.txt` for how to enable Windows Long Path support, or just work from a shorter path (e.g. `C:\dev\ascent-analytics`) outside OneDrive.

Then generate the data, in order:

```bash
python -m src.generation.generate_reference_data
python -m src.generation.generate_transactions
python -m src.generation.generate_extensions
```

## 🗺️ Roadmap

- [x] Project skeleton & tooling
- [x] Business problem & KPI definition
- [x] Synthetic data generation (~7 years, ~30k bookings)
  - [x] Reference data: Region, Guide, Route
  - [x] Transactional data: ScheduledTour, Booking, Payment
  - [x] Extension data: Review, Weather, Marketing, WebsiteAnalytics, EquipmentHire
- [ ] Data cleaning & validation pipeline (Python)
  - [x] Core entities: Region, Guide, Route, ScheduledTour, Booking, Payment
  - [ ] Extension entities: Review, Weather, Marketing, WebsiteAnalytics, EquipmentHire
- [ ] Dimensional model design (star schema)
- [ ] SQL warehouse build (schema, views, procedures, indexes)
- [ ] Power BI semantic model & DAX measures
- [ ] Dashboards: Executive, Sales, Customer, Guide, Route, Marketing, Operations, Finance, Data Quality
- [ ] Written insight report & recommendations
- [ ] Full documentation pass (architecture, data dictionary, KPI catalogue)

## 📌 Notes on Realism & Scope

This project favours **credibility over scale**. UK Summit Guides is a small guiding operation with groups capped at 3 people — so the dataset targets ~7 years of history and ~30,000 bookings rather than an inflated multi-million-row figure. Every entity that extends beyond the real UK Summit Guides schema (weather, marketing, website analytics, equipment hire, reviews) is clearly labelled as a synthetic extension, both here and in the data dictionary, so the provenance of every field is honest and traceable.