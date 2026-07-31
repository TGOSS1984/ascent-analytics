"""Tests for the extension-layer cleaning pipeline."""

import pandas as pd
import pytest

from src.cleaning.clean_extensions import (
    clean_booking_attribution,
    clean_equipment_hire,
    clean_marketing,
    clean_reviews,
    clean_website_analytics,
    clean_weather,
)
from src.cleaning.clean_reference import clean_regions
from src.cleaning.clean_transactions import clean_bookings, clean_scheduled_tours
from src.cleaning.clean_reference import clean_routes
from src.cleaning.quality_log import QualityLog
from src.cleaning.schemas import EXTENSION_SCHEMAS
from src.generation import config


def _require_raw(*filenames):
    for name in filenames:
        path = config.RAW_DATA_DIR / name
        if not path.exists():
            pytest.skip(f"{path} not found — run all three generation scripts first.")


@pytest.fixture(scope="module")
def cleaned_core():
    _require_raw("regions_raw.csv", "routes_raw.csv", "scheduled_tours_raw.csv", "bookings_raw.csv")
    log = QualityLog()
    regions = clean_regions(pd.read_csv(config.RAW_DATA_DIR / "regions_raw.csv"), log)
    routes = clean_routes(pd.read_csv(config.RAW_DATA_DIR / "routes_raw.csv"), log)
    tours = clean_scheduled_tours(pd.read_csv(config.RAW_DATA_DIR / "scheduled_tours_raw.csv"), routes, log)
    bookings = clean_bookings(pd.read_csv(config.RAW_DATA_DIR / "bookings_raw.csv"), tours, log)
    return regions, bookings


@pytest.fixture(scope="module")
def cleaned_extensions(cleaned_core):
    regions, bookings = cleaned_core
    _require_raw(
        "reviews_raw.csv", "weather_raw.csv", "booking_attribution_raw.csv",
        "marketing_raw.csv", "website_analytics_raw.csv", "equipment_hire_raw.csv",
    )
    log = QualityLog()
    reviews = clean_reviews(pd.read_csv(config.RAW_DATA_DIR / "reviews_raw.csv"), bookings, log)
    weather = clean_weather(pd.read_csv(config.RAW_DATA_DIR / "weather_raw.csv"), regions, log)
    attribution = clean_booking_attribution(
        pd.read_csv(config.RAW_DATA_DIR / "booking_attribution_raw.csv"), bookings, log
    )
    marketing = clean_marketing(pd.read_csv(config.RAW_DATA_DIR / "marketing_raw.csv"), log)
    website = clean_website_analytics(pd.read_csv(config.RAW_DATA_DIR / "website_analytics_raw.csv"), log)
    equipment = clean_equipment_hire(pd.read_csv(config.RAW_DATA_DIR / "equipment_hire_raw.csv"), bookings, log)
    return {
        "Review": reviews, "Weather": weather, "BookingAttribution": attribution,
        "Marketing": marketing, "WebsiteAnalytics": website, "EquipmentHire": equipment,
    }


def test_all_extension_tables_pass_their_schema(cleaned_extensions):
    for name, df in cleaned_extensions.items():
        EXTENSION_SCHEMAS[name].validate(df, lazy=True)


def test_reviews_reference_real_bookings(cleaned_extensions, cleaned_core):
    _, bookings = cleaned_core
    assert cleaned_extensions["Review"]["booking_id"].isin(bookings["booking_id"]).all()


def test_weather_regions_match_cleaned_region_names(cleaned_extensions, cleaned_core):
    regions, _ = cleaned_core
    assert cleaned_extensions["Weather"]["region"].isin(regions["name"]).all()


def test_booking_attribution_channels_are_closed_enum(cleaned_extensions):
    valid = set(config.MARKETING_CHANNELS.keys())
    assert set(cleaned_extensions["BookingAttribution"]["channel"]).issubset(valid)


def test_website_bounce_and_conversion_rates_bounded(cleaned_extensions):
    df = cleaned_extensions["WebsiteAnalytics"]
    assert df["bounce_rate"].between(0, 1).all()
    assert df["conversion_rate"].between(0, 1).all()


def test_equipment_hire_revenue_never_negative(cleaned_extensions):
    assert (cleaned_extensions["EquipmentHire"]["hire_revenue"] >= 0).all()


def test_marketing_zero_spend_channels_still_zero_after_cleaning(cleaned_extensions):
    df = cleaned_extensions["Marketing"]
    zero_spend_channels = {c for c, v in config.MARKETING_CHANNELS.items() if v[1] == 0.0}
    subset = df[df["channel"].isin(zero_spend_channels)]
    assert (subset["spend"] == 0.0).all()