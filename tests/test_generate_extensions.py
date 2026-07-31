"""Sanity tests for the synthetic extension-layer generators (Review,
Weather, Marketing/attribution, WebsiteAnalytics, EquipmentHire)."""

import random

import numpy as np
import pytest

from src.generation import config
from src.generation.generate_extensions import (
    generate_booking_attribution,
    generate_equipment_hire,
    generate_marketing,
    generate_reviews,
    generate_weather,
    generate_website_analytics,
    load_core_raw,
)


@pytest.fixture(scope="module")
def core_raw():
    try:
        return load_core_raw()
    except FileNotFoundError:
        pytest.skip(
            "Core raw CSVs not found — run generate_reference_data and "
            "generate_transactions before the extensions tests."
        )


def _rngs(offset=200):
    return random.Random(config.RANDOM_SEED + offset), np.random.default_rng(config.RANDOM_SEED + offset)


def test_every_review_references_a_real_booking(core_raw):
    _, _, bookings_df = core_raw
    rng, np_rng = _rngs()
    reviews_df = generate_reviews(bookings_df, rng, np_rng)
    assert set(reviews_df["booking_id"]).issubset(set(bookings_df["booking_id"]))


def test_review_ratings_within_valid_range(core_raw):
    _, _, bookings_df = core_raw
    rng, np_rng = _rngs()
    reviews_df = generate_reviews(bookings_df, rng, np_rng)
    for col in ["overall_rating", "guide_rating", "route_rating", "safety_rating", "value_rating"]:
        non_null = reviews_df[col].dropna()
        assert non_null.between(1, 5).all()


def test_weather_covers_every_region_and_full_date_range():
    rng, np_rng = _rngs()
    weather_df = generate_weather(rng, np_rng)
    assert set(weather_df["region_raw"].str.strip().str.title()) == set(config.REGION_CLIMATE.keys())
    n_days = (weather_df["date"].max() - weather_df["date"].min()).days + 1
    expected_days = len(weather_df) // len(config.REGION_CLIMATE)
    assert abs(n_days - expected_days) <= 1


def test_every_booking_gets_exactly_one_channel(core_raw):
    _, _, bookings_df = core_raw
    rng, np_rng = _rngs()
    attribution_df = generate_booking_attribution(bookings_df, rng, np_rng)
    assert len(attribution_df) == len(bookings_df)
    assert attribution_df["booking_id"].is_unique


def test_marketing_conversions_reconcile_with_attribution(core_raw):
    _, _, bookings_df = core_raw
    rng, np_rng = _rngs()
    attribution_df = generate_booking_attribution(bookings_df, rng, np_rng)
    marketing_df = generate_marketing(bookings_df, attribution_df, rng, np_rng)
    # every attributed booking should be accounted for in some campaign row
    assert marketing_df["conversions"].sum() == len(attribution_df)


def test_zero_spend_channels_have_no_cost(core_raw):
    _, _, bookings_df = core_raw
    rng, np_rng = _rngs()
    attribution_df = generate_booking_attribution(bookings_df, rng, np_rng)
    marketing_df = generate_marketing(bookings_df, attribution_df, rng, np_rng)
    zero_spend_channels = {c for c, v in config.MARKETING_CHANNELS.items() if v[1] == 0.0}
    subset = marketing_df[marketing_df["channel_raw"].str.strip().str.lower().isin(zero_spend_channels)]
    parsed_spend = (
        subset["spend_raw"].astype(str)
        .str.replace("£", "", regex=False)
        .str.replace("GBP", "", regex=False)
        .str.replace(",", "", regex=False)
        .str.strip()
        .astype(float)
    )
    assert (parsed_spend == 0.0).all()


def test_website_analytics_rates_are_valid_fractions():
    rng, np_rng = _rngs()
    website_df = generate_website_analytics(rng, np_rng)
    assert website_df["bounce_rate"].between(0, 1).all()
    assert website_df["conversion_rate"].between(0, 1).all()


def test_equipment_hire_only_for_completed_bookings(core_raw):
    _, _, bookings_df = core_raw
    rng, np_rng = _rngs()
    equipment_df = generate_equipment_hire(bookings_df, rng, np_rng)
    completed_ids = set(
        bookings_df[bookings_df["status_clean"].isin(["confirmed", "amended"])]["booking_id"]
    )
    assert set(equipment_df["booking_id"]).issubset(completed_ids)