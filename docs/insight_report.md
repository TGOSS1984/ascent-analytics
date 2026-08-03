# Ascent Analytics — Insight Report

**Prepared for:** UK Summit Guides leadership team
**Covering:** January 2019 – December 2025 (7 years of trading)
**Source:** Ascent Analytics warehouse — 28,982 bookings, 53 routes, 7 regions, 22 guides

This report answers the ten business questions set out in [`docs/business_problem.md`](business_problem.md) using the data actually sitting in the warehouse — every figure below is a real query result, not an estimate. Where the underlying data is synthetic (see *Scope & Limitations* at the end), the patterns and relationships are the point, not the exact pound figures.

---

## Executive Summary

- **Revenue has grown 125% since 2019** (£530K → £1.19M), recovering fully from a 45% COVID-era drop in 2020 and compounding at 10-62% year-on-year since.
- **Bank holidays generate 2.5x the revenue of a regular weekday**; weekends run at 1.7x. Demand is highly predictable by calendar day — an opportunity for proactive guide scheduling, not just reactive booking.
- **Route difficulty measurably affects both safety perception and cancellation risk**: advanced routes cancel 26% more often than moderate ones and rate 0.5 stars lower — worth pricing and communicating deliberately, not treating as noise.
- **Guide discounting doesn't clearly hurt performance** — the guide with the highest discount tendency in the roster is also one of the highest revenue earners. Discounting looks more like a business-as-usual sales lever than a red flag, though margin, not just revenue, should be the next thing checked.
- **Customer repeat rate sits at 4.55%** — low for a leisure business, but plausible for high-value, low-frequency adventure travel rather than a subscription-style product. Worth benchmarking against comparable operators before treating it as a problem.
- **Email marketing is the standout efficient channel** (63x ROAS on a small budget) and is almost certainly under-invested relative to its return.

---

## 1. Revenue & Growth

| Year | Revenue | YoY Growth |
|---|---|---|
| 2019 | £529,932 | — |
| 2020 | £289,807 | **-45.3%** |
| 2021 | £466,571 | +61.0% |
| 2022 | £755,376 | +61.9% |
| 2023 | £928,384 | +22.9% |
| 2024 | £1,082,321 | +16.6% |
| 2025 | £1,192,902 | +10.2% |

The business took a genuine, severe hit in 2020 (down 45%) and recovered fast — back above 2019 levels within a year, and growing every year since. Growth has decelerated from the 60%+ recovery years to a steadier 10-17% as the business matures, which is expected and healthy rather than a warning sign, but worth watching: if 2026 growth drops meaningfully below 10%, that's the point to investigate whether growth is structurally slowing or just a blip.

**Recommendation:** Use 2022-2023's 60%+ growth as the recovery baseline, not the ongoing target — budget and hiring plans built on 2023-era growth rates will overshoot.

## 2. Seasonality & Demand Timing

| Day type | Avg. revenue/day |
|---|---|
| Regular weekday | £1,742 |
| Weekend | £2,898 (**1.7x**) |
| Bank holiday | £4,419 (**2.5x**) |

This is the clearest, most actionable pattern in the whole dataset. Demand isn't just "seasonal" in the broad summer/winter sense — it's sharply concentrated on specific, entirely predictable calendar dates. A business that staffs evenly across the week is structurally under-guided on bank holidays and over-guided on quiet weekdays.

**Recommendation:** Build guide rostering around the UK bank holiday calendar explicitly, not just general seasonal demand. Consider premium pricing on bank holiday dates (the demand is already there — this is a margin opportunity, not just a capacity one) and off-peak weekday incentives (multi-day discounts, midweek-only routes) to smooth the trough.

## 3. Regional & Route Performance

| Region | Revenue | Bookings |
|---|---|---|
| Snowdonia | £1,596,556 | 7,093 |
| Lake District | £1,458,640 | 7,007 |
| Scottish Highlands | £801,119 | 2,998 |
| Brecon Beacons | £463,968 | 2,432 |
| Peak District | £454,748 | 2,324 |
| Cairngorms | £392,473 | 1,437 |
| Yorkshire Dales | £77,790 | 409 |

Snowdonia and the Lake District together generate 58% of all revenue — the business is genuinely concentrated in two regions, not evenly spread across seven. The single highest-earning route is **Snowdon Horseshoe** (£199,731), followed by Cadair Idris via Minffordd Path and Scafell Pike via Corridor Route — all three in the two lead regions.

Yorkshire Dales is the clear outlier at £77,790 — but this region only has one route in the current catalogue (Ingleborough), so low revenue reflects limited route choice, not weak regional demand. Not a finding to act on yet; a finding to gather more data on first.

**Recommendation:** Before investing further marketing spend into the Scottish Highlands/Cairngorms/Brecon Beacons/Peak District/Yorkshire Dales tail, test whether it's genuinely lower demand or simply a thinner route catalogue — Yorkshire Dales in particular needs more routes before any conclusion about regional appetite is fair.

## 4. Difficulty, Safety & Satisfaction

| Difficulty | Avg. rating | Cancellation rate |
|---|---|---|
| Moderate | 4.27★ | 13.2% |
| Hard | 4.12★ | 13.9% |
| Advanced | 3.77★ | 16.6% |

Harder routes cancel more often and rate lower — a real, measurable relationship, not noise (a 0.5-star gap and a 26% relative increase in cancellation rate between moderate and advanced is a meaningful spread, not statistical wobble). This likely reflects a combination of genuinely tougher conditions, higher weather sensitivity, and higher physical demand on both guides and customers.

**Recommendation:** Don't treat "advanced" as a single undifferentiated tier. Consider clearer pre-booking expectation-setting for advanced routes (fitness/experience prerequisites, weather contingency communication) — the goal isn't to avoid cancellations on hard routes, it's to reduce the *unexpected* ones that hurt satisfaction most.

## 5. Guide Performance & Discounting

The top five guides by discount tendency range from 8.0% to 9.3% — meaning even the most discount-prone guide in the roster still charges full price on roughly 90% of their bookings. Critically, **discount tendency does not clearly predict revenue**: Fraser Davies (8.4% tendency) generated £688,371, the highest revenue among the top-5 discounters, while Gwen Sinclair (9.3% tendency, the single highest in the business) generated a comparatively modest £146,332.

This means discounting behaviour and revenue generation are largely independent — a guide's willingness to discount says little about how much business they bring in.

**Recommendation:** Don't treat discount tendency as a performance red flag on its own. The real open question this data can't answer yet is **margin** — a guide bringing in £688K at an 8.4% average discount may still be more profitable than one bringing in £150K at 2%. Cross-reference discount tendency against `Net Profit` per guide, not revenue, before drawing conclusions about which guides to coach on pricing discipline.

## 6. Customer Behaviour

- **27,284 unique customers** across the dataset, of whom **1,070 (4.55%)** have booked more than once.
- This is a low repeat rate in absolute terms, but adventure guiding is a high-consideration, infrequent-purchase category (most people don't climb Snowdon every year) — a subscription-business benchmark would be the wrong comparison.

**Recommendation:** Before concluding repeat rate is "too low," benchmark against comparable adventure tourism operators — this figure may be entirely normal for the category. If it is genuinely low relative to peers, the next step is a win-back campaign targeted at the ~26,000 one-time customers, not a generic loyalty scheme.

## 7. Marketing Effectiveness

| Channel | Spend | Revenue | ROAS |
|---|---|---|---|
| Organic | £0 | £1,267,724 | — (no media cost) |
| Paid Social | £85,802 | £1,128,236 | **13.2x** |
| Paid Search | £114,486 | £1,071,419 | **9.4x** |
| Direct | £0 | £1,064,435 | — |
| Referral | £0 | £643,533 | — |
| Email | £5,117 | £322,989 | **63.1x** |

Email is dramatically more efficient than every paid channel — 63x ROAS on a budget that's a fraction of paid search or social spend. Even accounting for email typically converting an already-warm audience (existing customers/subscribers, not cold traffic), a return this far ahead of the next-best paid channel suggests the business is under-investing in it.

**Recommendation:** Test increasing email marketing spend and measure whether ROAS holds as volume scales (efficiency often drops as you push more spend through a channel — this needs validating, not assuming). Paid search's 9.4x ROAS is respectable but the weakest of the three paid/trackable channels — worth a closer look at whether spend is going to the right keywords before scaling it further.

## 8. Weather & Operational Resilience

**11.5% of all cancellations coincide with a storm warning or heavy rain (>15mm) on that date/region** — meaning the large majority of cancellations (88.5%) are driven by something other than weather (customer choice, guide availability, low numbers). Weather is a real but secondary cancellation driver, not the primary one.

**Recommendation:** Don't over-invest in weather-contingency planning at the expense of addressing the more common cancellation causes (see Section 4 — difficulty-driven cancellation is a bigger lever). Equipment hire, incidentally, is a healthy secondary revenue line at **£254,555** across the period — worth checking whether hire pricing has kept pace with cost inflation given it's rarely the focus of pricing reviews.

## 9. Financial Health

- **12.68% of confirmed/amended bookings had a discount applied**, totalling **£50,850** given away — **0.92% of gross revenue**. Modest at the company level, even though individual guides vary substantially (Section 5).
- **Payment health:** 23,337 payments succeeded (£5.16M), against 551 failed (£126K) and 570 stuck in refund_pending (£128K) — a **97.7% payment success rate** (paid ÷ (paid + failed)) is solid, but the £128K sitting in refund_pending is worth a process review: is this normal processing lag, or a backlog?
- **Refund rate: 11.06%** of paid bookings — consistent with the 14.2% overall cancellation rate (not every cancellation results in a refund; some are pre-payment).

**Recommendation:** The refund_pending balance (£128K, 570 payments) is the one figure here that looks more like an operational question than a strategic one — worth a finance team conversation about typical refund processing time before assuming it's a problem.

## 10. Data Quality

Every table in the warehouse passes its validation schema with **zero failures**, and completeness sits at 97-100% across all 12 core/extension tables (see `docs/data_quality/README.md` for the full audit trail). This report's figures can be trusted at face value — they're not built on top of known data quality gaps.

---

## Prioritised Recommendations

1. **Build guide rostering around the UK bank holiday calendar** — the single clearest, most actionable pattern in the data (2.5x demand multiplier, entirely predictable in advance).
2. **Test increased email marketing spend** — the most under-leveraged high-ROAS channel by a wide margin.
3. **Cross-reference guide discount tendency against margin, not revenue** — the current data can't say whether discounting is helping or hurting profitability, only that it doesn't clearly hurt topline revenue.
4. **Investigate the Yorkshire Dales/regional route catalogue gap** before drawing conclusions about regional demand — thin route selection, not weak demand, is the more likely explanation for the smallest region's low revenue.
5. **Review the £128K refund_pending balance** with finance — likely a process question, not a red flag, but worth confirming.
6. **Benchmark the 4.55% repeat customer rate** against comparable adventure tourism operators before treating it as underperformance.

---

## Scope & Limitations

This report is built on the **synthetic dataset** generated for the Ascent Analytics portfolio project (see `docs/data_dictionary/README.md` for full provenance of every field). Core entities (routes, guides, bookings, payments) are aligned to the real UK Summit Guides application schema; several tables (weather, marketing, equipment hire, website analytics, guide discount tendency) are synthetic extensions built to demonstrate a fuller analytics platform, clearly documented as such throughout the project.

**What this means practically:** the *relationships and patterns* described above (bank holiday demand spikes, difficulty-driven cancellation risk, channel ROAS differences) are the meaningful output of this analysis — they were deliberately built into the generation logic to be realistic and are genuinely present in the data. The *exact pound figures* should be read as illustrative of what a real analysis would surface, not as literal historical performance of the real business. If this pipeline were pointed at real UK Summit Guides data, the same queries and the same analytical approach would apply directly.