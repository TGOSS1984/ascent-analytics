"""Tests for the reporting views, the Python 'procedures' equivalent, and
the analytical query library — all executed against the live warehouse
built by build_warehouse.py + apply_views.py."""

import glob
import sqlite3

import pytest

from src.generation import config
from src.warehouse.procedures import (
    guide_performance_report,
    refresh_customer_ltv_snapshot,
    route_performance_report,
)

DB_PATH = config.WAREHOUSE_DIR / "ascent_analytics.db"
VIEWS = [
    "vw_bookings_enriched", "vw_monthly_revenue", "vw_route_performance",
    "vw_guide_performance", "vw_customer_summary", "vw_weather_flagged_cancellations",
    "vw_marketing_performance",
]


@pytest.fixture(scope="module")
def conn():
    if not DB_PATH.exists():
        pytest.skip(f"{DB_PATH} not found — run build_warehouse.py first.")
    connection = sqlite3.connect(DB_PATH)
    views_sql = (config.PROJECT_ROOT / "sql" / "views" / "01_reporting_views.sql").read_text()
    connection.executescript(views_sql)
    connection.commit()
    yield connection
    connection.close()


def test_every_view_exists_and_returns_rows(conn):
    for view in VIEWS:
        count = conn.execute(f"SELECT COUNT(*) FROM {view}").fetchone()[0]
        assert count > 0, f"{view} returned no rows"


def test_monthly_revenue_view_totals_match_factbookings(conn):
    view_total = conn.execute(
        "SELECT SUM(revenue) FROM vw_monthly_revenue"
    ).fetchone()[0]
    fact_total = conn.execute(
        "SELECT SUM(total_price) FROM FactBookings WHERE status = 'confirmed'"
    ).fetchone()[0]
    assert round(view_total, 2) == round(fact_total, 2)


def test_customer_summary_repeat_flag_is_binary(conn):
    bad = conn.execute(
        "SELECT COUNT(*) FROM vw_customer_summary WHERE is_repeat_customer NOT IN (0, 1)"
    ).fetchone()[0]
    assert bad == 0


def test_all_query_library_files_execute_without_error(conn):
    query_files = sorted(glob.glob(str(config.PROJECT_ROOT / "sql" / "queries" / "*.sql")))
    assert len(query_files) >= 8
    for path in query_files:
        sql = open(path).read()
        rows = conn.execute(sql).fetchall()
        assert isinstance(rows, list)  # executes without raising, returns something iterable


def test_guide_performance_report_runs(conn):
    df = guide_performance_report(conn, guide_id=1, year=2024)
    assert len(df) == 1
    assert "revenue" in df.columns


def test_route_performance_report_runs(conn):
    df = route_performance_report(conn, route_id=1)
    assert len(df) == 1
    assert df["bookings"].iloc[0] > 0


def test_refresh_customer_ltv_snapshot_populates_table(conn):
    result = refresh_customer_ltv_snapshot(conn)
    assert result["customers_refreshed"].iloc[0] > 0
    row_count = conn.execute("SELECT COUNT(*) FROM CustomerLifetimeValueSnapshot").fetchone()[0]
    assert row_count == result["customers_refreshed"].iloc[0]