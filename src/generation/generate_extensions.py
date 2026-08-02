"""
Generate raw (intentionally messy) synthetic extension data: Review,
Weather, Marketing (+ booking-channel attribution), WebsiteAnalytics,
EquipmentHire.

None of these tables exist in the live UK Summit Guides application — see
docs/data_dictionary/README.md for why they're included and how each is
tagged. Booking channel attribution is deliberately generated as its own
small table (booking_id -> channel) rather than added as a column onto
Booking, so the Core Booking table stays byte-for-byte aligned to the real
Django model.

Depends on the raw CSVs already written by generate_reference_data.py and
generate_transactions.py (reads them from data/raw/ rather than
regenerating in-memory, since Review/EquipmentHire need to know which
bookings actually happened, and Weather needs each tour's region + date).

Run directly (after the previous two generation steps):
    python -m src.generation.generate_extensions
"""

import random

import numpy as np
import pandas as pd
from faker import Faker

from src.generation import config
from src.utils import messiness


# ---------------------------------------------------------------------------
# Load core raw data
# ---------------------------------------------------------------------------

def load_core_raw():
    routes_df = pd.read_csv(config.RAW_DATA_DIR / "routes_raw.csv")
    tours_df = pd.read_csv(config.RAW_DATA_DIR / "scheduled_tours_raw.csv", parse_dates=["date"])
    bookings_df = pd.read_csv(config.RAW_DATA_DIR / "bookings_raw.csv", parse_dates=["created_at"])

    routes_df["region_clean"] = routes_df["region_name_raw"].str.strip().str.title()
    routes_df["difficulty_clean"] = routes_df["difficulty_raw"].str.strip().str.lower()

    tours_df = tours_df.merge(
        routes_df[["route_id", "region_clean", "difficulty_clean"]], on="route_id", how="left"
    )
    tours_df["status_clean"] = tours_df["status_raw"].str.strip().str.lower()

    bookings_df = bookings_df.merge(
        tours_df[["tour_id", "date", "season", "region_clean", "difficulty_clean"]], on="tour_id", how="left"
    )
    bookings_df["status_clean"] = bookings_df["status_raw"].str.strip().str.lower()

    def _parse_price(v):
        if isinstance(v, str):
            return float(v.replace("£", "").replace("GBP", "").strip())
        return float(v)

    bookings_df["total_price_clean"] = bookings_df["total_price_raw"].apply(_parse_price)

    return routes_df, tours_df, bookings_df


# ---------------------------------------------------------------------------
# Review
# ---------------------------------------------------------------------------

def generate_reviews(bookings_df, rng, np_rng):
    eligible = bookings_df[bookings_df["status_clean"].isin(["confirmed", "amended"])]
    n_reviews = int(len(eligible) * config.REVIEW_RESPONSE_RATE)
    reviewed = eligible.sample(n=n_reviews, random_state=config.RANDOM_SEED + 200)

    rows = []
    for booking in reviewed.itertuples(index=False):
        # winter tours skew slightly lower due to weather-related friction;
        # harder routes skew lower still, reflecting more demanding
        # conditions — see config.DIFFICULTY_RATING_ADJUSTMENT
        base_mean = 4.3 if booking.season == "summer" else 4.05
        base_mean += config.DIFFICULTY_RATING_ADJUSTMENT.get(booking.difficulty_clean, 0.0)
        overall = int(np.clip(round(np_rng.normal(base_mean, 0.85)), 1, 5))

        def _correlated(center, spread=0.9):
            return int(np.clip(round(np_rng.normal(center, spread)), 1, 5))

        guide_rating = _correlated(overall)
        route_rating = _correlated(overall)
        safety_rating = _correlated(max(overall, 4) if booking.season == "winter" else overall, spread=0.6)
        value_rating = _correlated(overall)

        would_recommend = overall >= 4 if rng.random() > 0.08 else overall >= 3
        comment_length = max(int(np_rng.normal(45 if overall in (1, 2, 5) else 25, 20)), 0)

        rows.append(
            {
                "booking_id": booking.booking_id,
                "overall_rating": messiness.maybe_null(overall, 0.02, rng),
                "guide_rating": messiness.maybe_null(guide_rating, 0.03, rng),
                "route_rating": messiness.maybe_null(route_rating, 0.03, rng),
                "safety_rating": messiness.maybe_null(safety_rating, 0.03, rng),
                "value_rating": messiness.maybe_null(value_rating, 0.03, rng),
                "comment_length": comment_length,
                "would_recommend_raw": messiness.mangle_casing(
                    "yes" if would_recommend else "no", rng
                ),
            }
        )
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Weather
# ---------------------------------------------------------------------------

def generate_weather(rng, np_rng):
    dates = pd.date_range(config.START_DATE, config.END_DATE, freq="D")
    rows = []
    for region, (summer_c, winter_c, storm_mult) in config.REGION_CLIMATE.items():
        for date in dates:
            day_of_year = date.dayofyear
            # smooth seasonal curve between winter and summer averages
            seasonal_pos = (1 - np.cos(2 * np.pi * (day_of_year - 15) / 365)) / 2
            avg_temp = winter_c + (summer_c - winter_c) * seasonal_pos
            temperature = round(np_rng.normal(avg_temp, 3.0), 1)

            is_winter_month = date.month in (11, 12, 1, 2, 3)
            rain_shape = 2.2 if is_winter_month else 1.3
            rain_mm = round(float(np_rng.gamma(rain_shape, 4.0)), 1)

            wind_speed = round(max(np_rng.normal(22 if is_winter_month else 14, 8) * storm_mult, 0), 1)
            visibility_km = round(np.clip(np_rng.normal(25 - rain_mm * 0.3, 6), 0.5, 40), 1)

            snow_depth_cm = 0.0
            if is_winter_month and temperature < 3:
                snow_depth_cm = round(max(np_rng.normal(8, 6), 0), 1)

            storm_prob = 0.015 * storm_mult * (1.8 if is_winter_month else 1.0)
            storm_warning = rng.random() < storm_prob

            rows.append(
                {
                    "date": date,
                    "region_raw": messiness.mangle_casing(region, rng),
                    "temperature_c": temperature,
                    "rain_mm": rain_mm,
                    "wind_speed_kmh": wind_speed,
                    "visibility_km": visibility_km,
                    "snow_depth_cm": snow_depth_cm,
                    "storm_warning": storm_warning,
                }
            )
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Booking attribution + Marketing
# ---------------------------------------------------------------------------

def generate_booking_attribution(bookings_df, rng, np_rng):
    channels = list(config.MARKETING_CHANNELS.keys())
    base_weights = np.array([config.MARKETING_CHANNELS[c][0] for c in channels])

    rows = []
    for booking in bookings_df.itertuples(index=False):
        year = booking.created_at.year
        weights = base_weights.copy()
        # paid_social share grows over time; organic share shrinks slightly
        social_idx = channels.index("paid_social")
        organic_idx = channels.index("organic")
        growth = min(max((year - 2019) * 0.02, 0), 0.12)
        weights[social_idx] += growth
        weights[organic_idx] -= growth * 0.6
        weights = np.clip(weights, 0.01, None)
        weights = weights / weights.sum()

        channel = rng.choices(channels, weights=weights.tolist())[0]
        rows.append({"booking_id": booking.booking_id, "channel_raw": messiness.mangle_casing(channel, rng)})

    return pd.DataFrame(rows)


def generate_marketing(bookings_df, attribution_df, rng, np_rng):
    merged = bookings_df.merge(attribution_df, on="booking_id", how="left")
    merged["channel_clean"] = merged["channel_raw"].str.strip().str.lower()
    merged["year_month"] = merged["created_at"].dt.to_period("M")

    grouped = (
        merged.groupby(["channel_clean", "year_month"])
        .agg(conversions=("booking_id", "count"), revenue=("total_price_clean", "sum"))
        .reset_index()
    )

    rows = []
    for row in grouped.itertuples(index=False):
        channel = row.channel_clean
        if channel not in config.MARKETING_CHANNELS:
            continue
        _, cpa, conv_rate, ctr = config.MARKETING_CHANNELS[channel]

        conversions = row.conversions
        spend = round(conversions * cpa * max(np_rng.normal(1.0, 0.15), 0.5), 2) if cpa > 0 else 0.0
        clicks = int(conversions / conv_rate * max(np_rng.normal(1.0, 0.1), 0.6)) if conv_rate > 0 else 0
        impressions = int(clicks / ctr) if ctr > 0 else int(clicks * rng.uniform(15, 40))

        campaign = rng.choice(config.CAMPAIGN_NAME_POOL.get(channel, [channel]))

        rows.append(
            {
                "campaign_raw": messiness.mangle_casing(campaign, rng),
                "channel_raw": messiness.mangle_casing(channel, rng),
                "year_month": str(row.year_month),
                "spend_raw": messiness.scramble_currency(spend, rng),
                "clicks": clicks,
                "impressions": impressions,
                "conversions": conversions,
                "revenue_raw": messiness.scramble_currency(round(row.revenue, 2), rng),
            }
        )
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# WebsiteAnalytics
# ---------------------------------------------------------------------------

def generate_website_analytics(rng, np_rng):
    weeks = pd.date_range(config.START_DATE, config.END_DATE, freq="W-MON")
    channels = list(config.MARKETING_CHANNELS.keys())
    devices = list(config.DEVICES.keys())

    rows = []
    for week in weeks:
        seasonal = 1.2 if week.month in (5, 6, 7, 8, 12) else 1.0
        for source in channels:
            source_weight = config.MARKETING_CHANNELS[source][0]
            base_sessions = 900 * source_weight * seasonal
            for device in devices:
                device_weight = config.DEVICES[device]
                sessions = max(int(np_rng.normal(base_sessions * device_weight, base_sessions * device_weight * 0.2)), 0)
                users = int(sessions * np_rng.uniform(0.75, 0.95))
                bounce_rate = round(
                    np.clip(np_rng.normal(0.62 if device == "mobile" else 0.48, 0.08), 0.1, 0.95), 3
                )
                conversion_rate = round(
                    np.clip(np_rng.normal(config.MARKETING_CHANNELS[source][2], 0.01), 0.001, 0.2), 4
                )
                browser = rng.choices(list(config.BROWSERS.keys()), weights=list(config.BROWSERS.values()))[0]
                country = rng.choices(
                    list(config.VISITOR_COUNTRIES.keys()), weights=list(config.VISITOR_COUNTRIES.values())
                )[0]
                country = messiness.typo_country_name(country, rng)

                rows.append(
                    {
                        "week_starting": week,
                        "traffic_source_raw": messiness.mangle_casing(source, rng),
                        "device_raw": messiness.mangle_casing(device, rng),
                        "sessions": sessions,
                        "users": users,
                        "bounce_rate": bounce_rate,
                        "conversion_rate": conversion_rate,
                        "browser": browser,
                        "country_raw": country,
                    }
                )
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# EquipmentHire
# ---------------------------------------------------------------------------

def generate_equipment_hire(bookings_df, rng, np_rng):
    eligible = bookings_df[bookings_df["status_clean"].isin(["confirmed", "amended"])]
    n_hires = int(len(eligible) * config.EQUIPMENT_HIRE_RATE)
    hiring = eligible.sample(n=n_hires, random_state=config.RANDOM_SEED + 300)

    rows = []
    for booking in hiring.itertuples(index=False):
        winter_advanced = booking.season == "winter" and booking.difficulty_clean in ("hard", "advanced")
        hired_flags = {}
        revenue = 0.0
        for item, (base_prob, price) in config.EQUIPMENT_ITEMS.items():
            prob = base_prob
            if item in ("ice_axe", "crampons") and winter_advanced:
                prob = min(prob * 2.5, 0.85)
            hired = rng.random() < prob
            hired_flags[item] = hired
            if hired:
                qty = rng.randint(1, max(int(booking.party_size), 1))
                revenue += qty * price

        rows.append(
            {
                "booking_id": booking.booking_id,
                **{f"{item}_raw": messiness.mangle_casing("yes" if v else "no", rng) for item, v in hired_flags.items()},
                "hire_revenue_raw": messiness.scramble_currency(round(revenue, 2), rng),
            }
        )
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    rng = random.Random(config.RANDOM_SEED + 200)
    np_rng = np.random.default_rng(config.RANDOM_SEED + 200)

    config.RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    routes_df, tours_df, bookings_df = load_core_raw()

    reviews_df = generate_reviews(bookings_df, rng, np_rng)
    weather_df = generate_weather(rng, np_rng)
    attribution_df = generate_booking_attribution(bookings_df, rng, np_rng)
    marketing_df = generate_marketing(bookings_df, attribution_df, rng, np_rng)
    website_df = generate_website_analytics(rng, np_rng)
    equipment_df = generate_equipment_hire(bookings_df, rng, np_rng)

    outputs = {
        "reviews_raw.csv": reviews_df,
        "weather_raw.csv": weather_df,
        "booking_attribution_raw.csv": attribution_df,
        "marketing_raw.csv": marketing_df,
        "website_analytics_raw.csv": website_df,
        "equipment_hire_raw.csv": equipment_df,
    }

    for filename, df in outputs.items():
        path = config.RAW_DATA_DIR / filename
        df.to_csv(path, index=False)
        print(f"Wrote {len(df):,} rows -> {path}")


if __name__ == "__main__":
    main()