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
    assert len(rows) == 7  # all seven regions represented (Yorkshire Dales added for real route coverage)
    assert all(revenue > 0 for _, revenue in rows)


def test_dimroute_has_valid_uk_coordinates(warehouse_conn):
    cur = warehouse_conn.cursor()
    rows = cur.execute("SELECT trailhead_lat, trailhead_lon FROM DimRoute").fetchall()
    assert len(rows) == 53  # 30 original synthetic + 27 real routes.json routes, minus 4 upgraded-in-place duplicates
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


def test_retail_week_starts_on_sunday(warehouse_conn):
    cur = warehouse_conn.cursor()
    rows = cur.execute("SELECT DISTINCT strftime('%w', week_start_date) FROM DimDate").fetchall()
    assert rows == [("0",)]  # SQLite %w: 0 = Sunday


def test_retail_week_number_resets_each_retail_year(warehouse_conn):
    cur = warehouse_conn.cursor()
    max_weeks = cur.execute("SELECT retail_year, MAX(week_number) FROM DimDate GROUP BY retail_year").fetchall()
    for year, max_week in max_weeks:
        assert 1 <= max_week <= 53


def test_bank_holidays_average_eight_per_year(warehouse_conn):
    cur = warehouse_conn.cursor()
    # only check years where DimDate has near-full coverage (>=300 days) —
    # excludes the partial boundary year DimDate extends into for a few
    # days (from payment/refund timestamps landing just past year-end)
    full_years = cur.execute(
        "SELECT year FROM DimDate GROUP BY year HAVING COUNT(*) >= 300"
    ).fetchall()
    full_year_set = {y for (y,) in full_years}
    holiday_counts = dict(
        cur.execute("SELECT year, COUNT(*) FROM DimDate WHERE is_bank_holiday = 1 GROUP BY year").fetchall()
    )
    assert len(full_year_set) > 0
    for year in full_year_set:
        assert holiday_counts.get(year) in (8, 9)


def test_revenue_meaningfully_higher_on_bank_holidays(warehouse_conn):
    cur = warehouse_conn.cursor()
    avg_by_flag = dict(
        cur.execute(
            """
            SELECT d.is_bank_holiday, AVG(daily.rev)
            FROM (
                SELECT tour_date_id, SUM(total_price) as rev
                FROM FactBookings WHERE status = 'confirmed'
                GROUP BY tour_date_id
            ) daily
            JOIN DimDate d ON daily.tour_date_id = d.date_id
            GROUP BY d.is_bank_holiday
            """
        ).fetchall()
    )
    assert avg_by_flag[1] > avg_by_flag[0] * 1.5  # bank holidays meaningfully higher, not just noise


def test_discount_tendency_correlates_with_actual_discount_rate(warehouse_conn):
    """Guides with a higher discount_tendency_pct should show a higher
    share of discounted bookings — confirms the guide-level trait
    actually drives booking-level behaviour, not just sitting unused."""
    cur = warehouse_conn.cursor()
    rows = cur.execute(
        """
        SELECT g.discount_tendency_pct, AVG(CAST(fb.discount_applied AS FLOAT)) as discount_rate
        FROM FactBookings fb JOIN DimGuide g ON fb.guide_id = g.guide_id
        GROUP BY g.guide_id
        HAVING COUNT(*) > 50
        """
    ).fetchall()
    tendencies = [r[0] for r in rows]
    rates = [r[1] for r in rows]
    # simple correlation check without needing numpy/scipy here
    mean_t, mean_r = sum(tendencies) / len(tendencies), sum(rates) / len(rates)
    cov = sum((t - mean_t) * (r - mean_r) for t, r in zip(tendencies, rates))
    assert cov > 0  # positive correlation


def test_total_price_never_exceeds_list_price_by_more_than_rounding_noise(warehouse_conn):
    """total_price should never exceed list_price by more than the
    whole-pound rounding noise the messiness layer can introduce (both
    fields can independently round to the nearest whole pound in raw
    data — see src/utils/messiness.scramble_currency) — a small number of
    ~£1 discrepancies are expected and already caught by the cleaning
    pipeline's own total_price_discount_mismatch metric. This test just
    guards against something structurally wrong (e.g. total_price
    exceeding list_price by a large margin, which would mean a real
    calculation bug, not rounding noise)."""
    cur = warehouse_conn.cursor()
    bad = cur.execute("SELECT COUNT(*) FROM FactBookings WHERE total_price > list_price + 1.50").fetchone()[0]
    assert bad == 0


def test_undiscounted_bookings_have_zero_discount_pct(warehouse_conn):
    cur = warehouse_conn.cursor()
    bad = cur.execute(
        "SELECT COUNT(*) FROM FactBookings WHERE discount_applied = 0 AND discount_pct != 0"
    ).fetchone()[0]
    assert bad == 0