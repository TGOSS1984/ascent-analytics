-- Reference stored procedures written for PostgreSQL (PL/pgSQL).
-- NOT executable against the SQLite warehouse used in this project — see
-- sql/procedures/README.md for why, and src/warehouse/procedures.py for
-- the SQLite-compatible equivalent that actually runs here.
--
-- These assume a Postgres warehouse built from the same star schema as
-- sql/schema/01_dimensions.sql and 02_facts.sql.

-- Returns a guide's performance summary for a given year.
CREATE OR REPLACE PROCEDURE sp_guide_performance_report(
    IN p_guide_id INTEGER,
    IN p_year INTEGER
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_full_name TEXT;
    v_bookings INTEGER;
    v_revenue NUMERIC;
    v_avg_rating NUMERIC;
BEGIN
    SELECT g.full_name INTO v_full_name
    FROM "DimGuide" g WHERE g.guide_id = p_guide_id;

    SELECT
        COUNT(*), COALESCE(SUM(fb.total_price), 0)
    INTO v_bookings, v_revenue
    FROM "FactBookings" fb
    JOIN "DimDate" d ON fb.tour_date_id = d.date_id
    WHERE fb.guide_id = p_guide_id
      AND d.year = p_year
      AND fb.status = 'confirmed';

    SELECT ROUND(AVG(fr.guide_rating), 2) INTO v_avg_rating
    FROM "FactReviews" fr
    JOIN "FactBookings" fb ON fr.booking_id = fb.booking_id
    JOIN "DimDate" d ON fb.tour_date_id = d.date_id
    WHERE fb.guide_id = p_guide_id AND d.year = p_year;

    RAISE NOTICE 'Guide: % | Year: % | Bookings: % | Revenue: £% | Avg rating: %',
        v_full_name, p_year, v_bookings, v_revenue, v_avg_rating;
END;
$$;

-- CALL sp_guide_performance_report(3, 2024);


-- Recomputes and upserts a materialised customer lifetime value summary
-- table (useful when CLV is queried often enough that recalculating it
-- from FactBookings on every request is wasteful).
CREATE TABLE IF NOT EXISTS "CustomerLifetimeValueSnapshot" (
    customer_id INTEGER PRIMARY KEY,
    lifetime_value NUMERIC NOT NULL,
    total_bookings INTEGER NOT NULL,
    last_refreshed TIMESTAMP NOT NULL DEFAULT now()
);

CREATE OR REPLACE PROCEDURE sp_refresh_customer_ltv_snapshot()
LANGUAGE plpgsql
AS $$
BEGIN
    TRUNCATE "CustomerLifetimeValueSnapshot";

    INSERT INTO "CustomerLifetimeValueSnapshot" (customer_id, lifetime_value, total_bookings)
    SELECT
        fb.customer_id,
        SUM(CASE WHEN fb.status = 'confirmed' THEN fb.total_price ELSE 0 END),
        COUNT(*)
    FROM "FactBookings" fb
    GROUP BY fb.customer_id;

    RAISE NOTICE 'Refreshed CLV snapshot for % customers', (SELECT COUNT(*) FROM "CustomerLifetimeValueSnapshot");
END;
$$;

-- CALL sp_refresh_customer_ltv_snapshot();