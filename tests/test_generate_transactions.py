"""Sanity tests for the transactional data generator (ScheduledTour,
Booking, Payment). As with the reference data tests, these check shape,
referential integrity, and determinism — not data quality, which is the
cleaning pipeline's job."""

import random

import numpy as np
import pandas as pd
from faker import Faker

from src.generation import config
from src.generation.generate_transactions import (
    assign_guide_tenure,
    build_reference_lookups,
    finalise_tour_status,
    generate_bookings_and_payments,
    generate_scheduled_tours,
)


def _build_small_dataset(n_years=1):
    rng = random.Random(config.RANDOM_SEED + 100)
    np_rng = np.random.default_rng(config.RANDOM_SEED + 100)
    faker = Faker("en_GB")
    Faker.seed(config.RANDOM_SEED)

    guides_df, routes_df = build_reference_lookups()
    guides_df = assign_guide_tenure(guides_df, np_rng)

    # shrink to a single year for a fast test run
    original_counts = dict(config.ANNUAL_TOUR_COUNTS)
    try:
        config.ANNUAL_TOUR_COUNTS.clear()
        config.ANNUAL_TOUR_COUNTS[2023] = 200
        tours_df = generate_scheduled_tours(guides_df, routes_df, rng, np_rng)
        bookings_df, payments_df, booked_spaces, had_booking = generate_bookings_and_payments(
            tours_df, rng, np_rng, faker
        )
        tours_df = finalise_tour_status(tours_df, booked_spaces, had_booking, rng)
    finally:
        config.ANNUAL_TOUR_COUNTS.clear()
        config.ANNUAL_TOUR_COUNTS.update(original_counts)

    return tours_df, bookings_df, payments_df


def test_tour_count_matches_config():
    tours_df, _, _ = _build_small_dataset()
    assert len(tours_df) == 200


def test_every_booking_references_a_real_tour():
    tours_df, bookings_df, _ = _build_small_dataset()
    assert set(bookings_df["tour_id"]).issubset(set(tours_df["tour_id"]))


def test_every_payment_references_a_real_booking():
    tours_df, bookings_df, payments_df = _build_small_dataset()
    assert set(payments_df["booking_id"]) == set(bookings_df["booking_id"])


def test_party_size_never_exceeds_three():
    _, bookings_df, _ = _build_small_dataset()
    assert bookings_df["party_size"].between(1, 3).all()


def test_tour_dates_within_configured_window():
    tours_df, _, _ = _build_small_dataset()
    dates = pd.to_datetime(tours_df["date"])
    assert dates.min() >= pd.Timestamp("2023-01-01")
    assert dates.max() <= pd.Timestamp("2023-12-31")