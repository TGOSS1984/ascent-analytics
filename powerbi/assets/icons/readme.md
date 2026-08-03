# KPI Card Icons

36 icons, one per card visual built across all 10 dashboards (32 from the original build, plus 4 more added during a later pass — Bank Holiday Uplift and the 3 discount cards). Sourced from [Lucide](https://lucide.dev) (ISC license — free to use, attribution appreciated but not required) and recoloured to the theme's ice-blue accent (`#B0CFD0`) so they sit naturally on the dark card background alongside everything else in `powerbi/assets/`.

Each is a 256×256 transparent PNG, ready to drop straight onto a card via **Insert → Image**.

## How to place one

1. Insert → Image → browse to the relevant file below → Open
2. Drag it to the top-right corner of the matching card, resize to roughly 24-32px (small — it's an accent, not the focus)
3. Repeat per card

There's no way to batch-apply these across many cards at once in Power BI — it's genuinely one at a time, same as the card-caption-colour fix. Budget a few minutes per dashboard page.

## Mapping

| File | Card | Dashboard |
|---|---|---|
| `revenue.png` | Revenue | Executive |
| `net-profit.png` | Net Profit | Executive |
| `net-profit-margin.png` | Net Profit Margin | Executive, Finance |
| `total-bookings.png` | Total Bookings | Executive |
| `average-customer-satisfaction.png` | Average Customer Satisfaction | Executive |
| `revenue-growth.png` | Revenue Growth % | Sales |
| `total-customers.png` | Total Customers | Customer |
| `repeat-customer-rate.png` | Repeat Customer Rate | Customer |
| `average-reviews-per-booking.png` | Average Reviews per Confirmed Booking | Customer |
| `highest-revenue-route.png` | Highest Revenue Route | Route |
| `most-popular-route.png` | Most Popular Route | Route |
| `occupancy.png` | Occupancy % | Route |
| `average-overall-rating.png` | Average Overall Rating | Route |
| `marketing-spend.png` | Marketing Spend | Marketing |
| `marketing-revenue.png` | Marketing Revenue | Marketing |
| `roas.png` | ROAS / Blended ROAS | Marketing |
| `cac.png` | CAC | Marketing |
| `equipment-hire-rate.png` | Equipment Hire Rate | Operations |
| `equipment-hire-revenue.png` | Equipment Hire Revenue | Operations |
| `storm-warning-days.png` | Storm Warning Days | Operations |
| `guide-utilisation.png` | Guide Utilisation % | Operations (and Guide leaderboard table) |
| `weather-flagged-cancellation-rate.png` | Weather-Flagged Cancellation Rate | Operations |
| `gross-margin.png` | Gross Margin | Finance |
| `refund-rate.png` | Refund % | Finance |
| `payment-success-rate.png` | Payment Success Rate | Finance |
| `outstanding-balance.png` | Outstanding Balance | Finance |
| `total-sessions.png` | Total Sessions | Website Analytics |
| `total-users.png` | Total Users | Website Analytics |
| `average-bounce-rate.png` | Average Bounce Rate | Website Analytics |
| `average-conversion-rate.png` | Average Conversion Rate | Website Analytics |
| `total-validation-failures.png` | Total Validation Failures | Data Quality |
| `average-completeness.png` | Average Completeness % | Data Quality |
| `bank-holiday-uplift.png` | Revenue on Bank Holidays vs Regular Days | Executive |
| `average-price-per-tour.png` | Average Price per Tour | Finance |
| `total-discount-given.png` | Total Discount Given | Finance |
| `discount-pct-of-revenue.png` | Discount % of Revenue | Finance |

## Regenerating or adding more

If you add new cards later and want matching icons, the same pipeline works for any [Lucide icon name](https://lucide.dev/icons):

```bash
curl -s -o icon.svg https://raw.githubusercontent.com/lucide-icons/lucide/main/icons/ICON-NAME.svg
sed 's/currentColor/#B0CFD0/g' icon.svg > icon_colored.svg
python3 -c "import cairosvg; cairosvg.svg2png(url='icon_colored.svg', write_to='icon.png', output_width=256, output_height=256, background_color=None)"
```
