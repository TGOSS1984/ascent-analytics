"""
Parameterised, reusable query functions — the practical equivalent of
stored procedures for a SQLite warehouse (which has no CREATE PROCEDURE
support). See sql/procedures/README.md for the full explanation, and
sql/procedures/postgres_examples.sql for what these would look like as
real stored procedures on a production Postgres warehouse.

Each function takes an open sqlite3 connection and returns a pandas
DataFrame, so these compose naturally with notebooks, scripts, or a
future API layer.
"""

import sqlite3

import pandas as pd


def guide_performance_report(conn: sqlite3.Connection, guide_id: int, year: int) -> pd.DataFrame:
    """Equivalent of sp_guide_performance_report(guide_id, year)."""
    query = """
        SELECT
            g.full_name,
            :year AS report_year,
            COUNT(fb.booking_id) FILTER (WHERE fb.status = 'confirmed') AS bookings,
            COALESCE(SUM(CASE WHEN fb.status = 'confirmed' THEN fb.total_price ELSE 0 END), 0) AS revenue,
            ROUND(AVG(fr.guide_rating), 2) AS avg_guide_rating
        FROM DimGuide g
        LEFT JOIN FactBookings fb
            ON g.guide_id = fb.guide_id
            AND fb.tour_date_id BETWEEN :year * 10000 + 101 AND :year * 10000 + 1231
        LEFT JOIN FactReviews fr ON fb.booking_id = fr.booking_id
        WHERE g.guide_id = :guide_id
        GROUP BY g.full_name
    """
    return pd.read_sql_query(query, conn, params={"guide_id": guide_id, "year": year})


def refresh_customer_ltv_snapshot(conn: sqlite3.Connection) -> pd.DataFrame:
    """Equivalent of sp_refresh_customer_ltv_snapshot(). Recomputes CLV per
    customer and materialises it into CustomerLifetimeValueSnapshot,
    replacing whatever was there before — same idea as the Postgres
    TRUNCATE + INSERT version, just without a real stored procedure to
    wrap it in."""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS CustomerLifetimeValueSnapshot (
            customer_id INTEGER PRIMARY KEY,
            lifetime_value REAL NOT NULL,
            total_bookings INTEGER NOT NULL,
            last_refreshed TEXT NOT NULL
        )
        """
    )
    conn.execute("DELETE FROM CustomerLifetimeValueSnapshot")
    conn.execute(
        """
        INSERT INTO CustomerLifetimeValueSnapshot (customer_id, lifetime_value, total_bookings, last_refreshed)
        SELECT
            customer_id,
            SUM(CASE WHEN status = 'confirmed' THEN total_price ELSE 0 END),
            COUNT(*),
            DATETIME('now')
        FROM FactBookings
        GROUP BY customer_id
        """
    )
    conn.commit()
    return pd.read_sql_query(
        "SELECT COUNT(*) AS customers_refreshed FROM CustomerLifetimeValueSnapshot", conn
    )


def route_performance_report(conn: sqlite3.Connection, route_id: int) -> pd.DataFrame:
    """A third example, not mirrored in the Postgres file — shows the
    pattern generalises to any parameterised report, not just the two
    ported examples."""
    query = """
        SELECT
            rt.name,
            rt.difficulty,
            COUNT(fb.booking_id) AS bookings,
            SUM(CASE WHEN fb.status = 'confirmed' THEN fb.total_price ELSE 0 END) AS revenue,
            ROUND(AVG(fr.overall_rating), 2) AS avg_rating
        FROM DimRoute rt
        LEFT JOIN FactBookings fb ON rt.route_id = fb.route_id
        LEFT JOIN FactReviews fr ON fb.booking_id = fr.booking_id
        WHERE rt.route_id = :route_id
        GROUP BY rt.name, rt.difficulty
    """
    return pd.read_sql_query(query, conn, params={"route_id": route_id})


if __name__ == "__main__":
    from src.generation import config

    conn = sqlite3.connect(config.WAREHOUSE_DIR / "ascent_analytics.db")
    print(guide_performance_report(conn, guide_id=1, year=2024))
    print(refresh_customer_ltv_snapshot(conn))
    conn.close()