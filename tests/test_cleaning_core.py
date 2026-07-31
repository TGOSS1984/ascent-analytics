"""Tests for the core cleaning pipeline: utils, and the Region/Guide/Route/
ScheduledTour/Booking/Payment cleaning functions."""

import pandas as pd
import pytest

from src.cleaning.clean_reference import clean_guides, clean_regions, clean_routes
from src.cleaning.clean_transactions import clean_bookings, clean_payments, clean_scheduled_tours
from src.cleaning.quality_log import QualityLog
from src.cleaning.schemas import CORE_SCHEMAS
from src.cleaning.utils import canonicalise_country, clean_email, dedupe, parse_currency, parse_distance_km
from src.generation import config


# ---------------------------------------------------------------------------
# Unit tests for shared helpers
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "raw,expected",
    [
        ("£99.95", 99.95),
        ("GBP 99.95", 99.95),
        ("99.95 GBP", 99.95),
        ("£1,133.78", 1133.78),
        (99.95, 99.95),
        (None, None),
    ],
)
def test_parse_currency(raw, expected):
    assert parse_currency(raw) == expected


def test_parse_distance_km_strips_unit():
    assert parse_distance_km("14.5 km") == 14.5
    assert parse_distance_km(14.5) == 14.5


def test_clean_email_repairs_at_substitution():
    fixed, invalid = clean_email("jane.doe at example.com")
    assert fixed == "jane.doe@example.com"
    assert invalid is False


def test_clean_email_flags_genuinely_broken_address():
    fixed, invalid = clean_email("not-an-email")
    assert invalid is True


def test_canonicalise_country_maps_known_variants():
    assert canonicalise_country("UK")[0] == "United Kingdom"
    assert canonicalise_country("U.K.")[0] == "United Kingdom"
    assert canonicalise_country("Neverland")[1] is True  # unrecognised, flagged


def test_dedupe_removes_exact_duplicates():
    df = pd.DataFrame({"id": [1, 1, 2], "val": ["a", "a", "b"]})
    out, n_removed = dedupe(df, subset="id")
    assert n_removed == 1
    assert len(out) == 2


# ---------------------------------------------------------------------------
# End-to-end pipeline tests (skipped if raw data hasn't been generated)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def raw_core():
    files = {}
    names = [
        "regions_raw.csv", "guides_raw.csv", "routes_raw.csv",
        "scheduled_tours_raw.csv", "bookings_raw.csv", "payments_raw.csv",
    ]
    for name in names:
        path = config.RAW_DATA_DIR / name
        if not path.exists():
            pytest.skip(f"{path} not found — run the generation scripts first.")
        files[name] = pd.read_csv(path)
    return files


@pytest.fixture(scope="module")
def cleaned_core(raw_core):
    log = QualityLog()
    regions = clean_regions(raw_core["regions_raw.csv"], log)
    guides = clean_guides(raw_core["guides_raw.csv"], log)
    routes = clean_routes(raw_core["routes_raw.csv"], log)
    tours = clean_scheduled_tours(raw_core["scheduled_tours_raw.csv"], routes, log)
    bookings = clean_bookings(raw_core["bookings_raw.csv"], tours, log)
    payments = clean_payments(raw_core["payments_raw.csv"], bookings, log)
    return {
        "Region": regions, "Guide": guides, "Route": routes,
        "ScheduledTour": tours, "Booking": bookings, "Payment": payments,
    }


def test_all_cleaned_tables_pass_their_schema(cleaned_core):
    for name, df in cleaned_core.items():
        CORE_SCHEMAS[name].validate(df, lazy=True)  # raises SchemaErrors on failure


def test_no_orphaned_foreign_keys(cleaned_core):
    assert cleaned_core["ScheduledTour"]["route_id"].isin(cleaned_core["Route"]["route_id"]).all()
    assert cleaned_core["Booking"]["tour_id"].isin(cleaned_core["ScheduledTour"]["tour_id"]).all()
    assert cleaned_core["Payment"]["booking_id"].isin(cleaned_core["Booking"]["booking_id"]).all()


def test_no_malformed_emails_remain(cleaned_core):
    assert not cleaned_core["Booking"]["contact_email_invalid"].any() or (
        cleaned_core["Booking"]["contact_email_invalid"].mean() < 0.01
    )


def test_route_difficulty_is_closed_enum(cleaned_core):
    assert set(cleaned_core["Route"]["difficulty"]).issubset({"moderate", "hard", "advanced"})


def test_payment_currency_is_canonical(cleaned_core):
    assert set(cleaned_core["Payment"]["currency"]) == {"GBP"}