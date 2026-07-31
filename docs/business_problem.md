# Business Problem & Stakeholder Goals

## 1. The business

UK Summit Guides is a small, boutique guided mountain tour operator working across UK regions (e.g. Snowdonia, the Lake District, the Scottish Highlands). Trips run in two seasons (`winter` / `summer`), across three difficulty tiers (`moderate` / `hard` / `advanced`), with groups deliberately kept small — a maximum of **3 clients per guide** per scheduled tour. Customers book and pay online; guides are a mix of employed and freelance.

Because it's a small operator, every booking, every guide-day, and every cancelled trip has a real, visible impact on revenue — there's no volume to hide behind. That's exactly why decisions need to be data-led rather than gut-feel.

## 2. Why this project exists

The live platform ([UK Summit Guides](https://github.com/TGOSS1984/uk-summit-guides)) captures transactional data — bookings, payments, routes, guides — but has no reporting layer. Operationally, the business currently can't easily answer questions like *"which route makes us the most money once we account for guide cost and cancellations?"* without someone manually pulling records.

Ascent Analytics exists to close that gap: take the operational data (and a small set of realistic synthetic extensions — marketing, weather, equipment, reviews — that a growing business would plausibly add next), and turn it into a governed, trustworthy reporting layer that a non-technical stakeholder can use to make decisions.

## 3. Stakeholders & their goals

| Stakeholder | Cares about | Primary dashboard(s) |
|---|---|---|
| **Managing Director** | Overall business health: revenue, profit, growth, risk | Executive |
| **Operations Manager** | Guide utilisation, scheduling efficiency, weather disruption, equipment logistics | Operations, Guide |
| **Marketing Lead** | Which channels bring bookings, at what cost, and which convert | Marketing, Website |
| **Finance** | Margins, refunds, outstanding payments, cost control | Finance |
| **Head Guide / Guide Lead** | Guide performance, safety ratings, fair workload distribution | Guide |
| **Customer Experience** | Satisfaction, repeat bookings, cancellation drivers | Customer, Route |

## 4. Core business questions

These are the questions the finished platform must be able to answer with evidence, not opinion:

1. Which routes are most profitable once guide cost and cancellations are accounted for?
2. Which guides consistently perform best — on revenue, ratings, and safety?
3. Which marketing channels generate bookings most cost-effectively?
4. Which customers return, and what predicts repeat bookings?
5. What causes cancellations, and can any of it be reduced operationally?
6. Which weather conditions measurably reduce bookings or force cancellations?
7. Which equipment is hired most, and is hire pricing leaving money on the table?
8. Which regions are growing versus stagnating?
9. Does tour difficulty correlate with customer satisfaction?
10. Is the business over- or under-utilising guide capacity across the season?

## 5. Success metrics (headline KPIs)

The KPI catalogue ([`docs/kpi_catalogue/README.md`](kpi_catalogue/README.md)) defines every metric in full. At a headline level, success for this platform means being able to report, on demand and with drill-down:

- **Revenue, Net Profit, and Net Margin** — overall and by route/region/guide/season
- **Booking Volume and Cancellation Rate**
- **Guide Utilisation** and **Guide Performance Index**
- **Customer Repeat Rate** and **Customer Lifetime Value**
- **Marketing ROAS** and **Cost per Booking**
- **Data Quality Score** for the warehouse itself

## 6. Scope & constraints

- **Data realism over data volume.** ~7 years of history, ~30,000 bookings — proportionate to a 3-person-per-trip guiding company, not an inflated headline number.
- **Provenance is documented.** Every table is tagged as either *aligned* to the real UK Summit Guides schema or a *synthetic extension* built to demonstrate a fuller warehouse — see the [data dictionary](data_dictionary/README.md).
- **Intentional messiness.** Raw data is generated with realistic quality issues (missing values, duplicate bookings, inconsistent country names, invalid ages, currency inconsistencies) so the cleaning pipeline has real work to do and can be documented honestly.
- **No PII.** All customer data is synthetic; no real individuals are represented.