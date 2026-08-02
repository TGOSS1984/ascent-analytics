"""Tests for the SQL warehouse build: schema creation and referential
integrity once the star schema is populated from the cleaned CSVs."""

import sqlite3

import pytest

from src.generation import config


@pytest.fixture(scope="module")
def warehouse_conn():
    db_path = config.WAREHOUSE_DIR / "ascent_analytics.db"
    if not db_path.exists():
        pytest.skip(f"{db_path} not found — run `python -m src.warehouse.build_warehouse` first.")
    conn = sqlite3.connect(db_path)
    yield conn
    conn.close()


TABLES = [
    "DimDate", "DimRegion", "DimGuide", "DimRoute", "DimCustomer", "DimMarketingChannel",
    "FactBookings", "FactPayments", "FactReviews", "FactEquipmentHire", "FactMarketing",
    "FactWebsiteAnalytics", "FactWeather",
]


def test_every_table_exists_and_has_rows(warehouse_conn):
    cur = warehouse_conn.cursor()
    for table in TABLES:
        count = cur.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        assert count > 0, f"{table} is empty"


def test_factbookings_foreign_keys_all_resolve(warehouse_conn):
    cur = warehouse_conn.cursor()
    orphan_customers = cur.execute(
        "SELECT COUNT(*) FROM FactBookings fb LEFT JOIN DimCustomer c ON fb.customer_id = c.customer_id WHERE c.customer_id IS NULL"
    ).fetchone()[0]
    orphan_routes = cur.execute(
        "SELECT COUNT(*) FROM FactBookings fb LEFT JOIN DimRoute r ON fb.route_id = r.route_id WHERE r.route_id IS NULL"
    ).fetchone()[0]
    orphan_regions = cur.execute(
        "SELECT COUNT(*) FROM FactBookings fb LEFT JOIN DimRegion r ON fb.region_id = r.region_id WHERE r.region_id IS NULL"
    ).fetchone()[0]
    orphan_dates = cur.execute(
        "SELECT COUNT(*) FROM FactBookings fb LEFT JOIN DimDate d ON fb.tour_date_id = d.date_id WHERE d.date_id IS NULL"
    ).fetchone()[0]
    assert orphan_customers == 0
    assert orphan_routes == 0
    assert orphan_regions == 0
    assert orphan_dates == 0


def test_factpayments_dates_resolve_within_dimdate_range(warehouse_conn):
    cur = warehouse_conn.cursor()
    orphan_paid = cur.execute(
        """
        SELECT COUNT(*) FROM FactPayments p
        LEFT JOIN DimDate d ON p.paid_date_id = d.date_id
        WHERE p.paid_date_id IS NOT NULL AND d.date_id IS NULL
        """
    ).fetchone()[0]
    assert orphan_paid == 0


def test_factreviews_ratings_bounded(warehouse_conn):
    cur = warehouse_conn.cursor()
    bad = cur.execute(
        "SELECT COUNT(*) FROM FactReviews WHERE overall_rating IS NOT NULL AND (overall_rating < 1 OR overall_rating > 5)"
    ).fetchone()[0]
    assert bad == 0


def test_fact_bookings_party_size_bounded(warehouse_conn):
    cur = warehouse_conn.cursor()
    bad = cur.execute("SELECT COUNT(*) FROM FactBookings WHERE party_size < 1 OR party_size > 3").fetchone()[0]
    assert bad == 0


def test_revenue_by_region_is_positive_and_populated(warehouse_conn):
    cur = warehouse_conn.cursor()
    rows = cur.execute(
        """
        SELECT r.name, SUM(fb.total_price) FROM FactBookings fb
        JOIN DimRegion r ON fb.region_id = r.region_id
        WHERE fb.status = 'confirmed'
        GROUP BY r.name
        """
    ).fetchall()
    assert len(rows) == 6  # all six regions represented
    assert all(revenue > 0 for _, revenue in rows)


def test_dimroute_has_valid_uk_coordinates(warehouse_conn):
    cur = warehouse_conn.cursor()
    rows = cur.execute("SELECT trailhead_lat, trailhead_lon FROM DimRoute").fetchall()
    assert len(rows) == 30
    for lat, lon in rows:
        assert 49.5 <= lat <= 61.0
        assert -8.5 <= lon <= 2.0


def test_rating_decreases_with_difficulty(warehouse_conn):
    """Confirms the difficulty-weighted review adjustment actually shows up
    in the warehouse — moderate should rate meaningfully higher than
    advanced, not be statistically flat as it was before this was added."""
    cur = warehouse_conn.cursor()
    rows = dict(
        cur.execute(
            """
            SELECT rt.difficulty, AVG(fr.overall_rating)
            FROM FactReviews fr JOIN DimRoute rt ON fr.route_id = rt.route_id
            GROUP BY rt.difficulty
            """
        ).fetchall()
    )
    assert rows["moderate"] > rows["hard"] > rows["advanced"]
    assert rows["moderate"] - rows["advanced"] > 0.3  # meaningfully different, not noise