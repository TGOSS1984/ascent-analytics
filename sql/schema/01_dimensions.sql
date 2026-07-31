-- Dimension tables for the Ascent Analytics warehouse.
-- Written for SQLite (the dev/demo target) but kept close to standard SQL
-- so it ports to Postgres/SQL Server with minimal changes (see the notes
-- at the bottom of this file).

PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS DimDate;
CREATE TABLE DimDate (
    date_id         INTEGER PRIMARY KEY,   -- YYYYMMDD
    full_date       DATE NOT NULL UNIQUE,
    day             INTEGER NOT NULL,
    month           INTEGER NOT NULL,
    month_name      TEXT NOT NULL,
    quarter         INTEGER NOT NULL,
    year            INTEGER NOT NULL,
    day_of_week     INTEGER NOT NULL,      -- 0 = Monday
    day_name        TEXT NOT NULL,
    is_weekend      BOOLEAN NOT NULL,
    calendar_season TEXT NOT NULL          -- Winter/Spring/Summer/Autumn (meteorological)
);

DROP TABLE IF EXISTS DimRegion;
CREATE TABLE DimRegion (
    region_id INTEGER PRIMARY KEY,
    name      TEXT NOT NULL UNIQUE,
    slug      TEXT NOT NULL UNIQUE
);

DROP TABLE IF EXISTS DimGuide;
CREATE TABLE DimGuide (
    guide_id          INTEGER PRIMARY KEY,
    first_name        TEXT NOT NULL,
    last_name         TEXT NOT NULL,
    full_name         TEXT NOT NULL,
    qualifications    TEXT,                -- nullable: genuine data gap, not imputed
    years_experience  INTEGER NOT NULL,
    languages         TEXT NOT NULL,
    employment_type   TEXT NOT NULL CHECK (employment_type IN ('employed', 'freelance')),
    day_rate_gbp      REAL NOT NULL,
    primary_region_id INTEGER NOT NULL REFERENCES DimRegion(region_id),
    active            BOOLEAN NOT NULL
);

DROP TABLE IF EXISTS DimRoute;
CREATE TABLE DimRoute (
    route_id          INTEGER PRIMARY KEY,
    name              TEXT NOT NULL,
    region_id         INTEGER NOT NULL REFERENCES DimRegion(region_id),
    difficulty        TEXT NOT NULL CHECK (difficulty IN ('moderate', 'hard', 'advanced')),
    distance_km       REAL NOT NULL,
    duration_hours    REAL NOT NULL,
    mountain_height_m INTEGER NOT NULL,
    elevation_gain_m  INTEGER NOT NULL,
    is_featured       BOOLEAN NOT NULL,
    active            BOOLEAN NOT NULL
);

-- Derived dimension — see docs/architecture/README.md for why this is
-- built from Booking.contact_email rather than sourced from a real
-- Customer table (the live application doesn't have one).
DROP TABLE IF EXISTS DimCustomer;
CREATE TABLE DimCustomer (
    customer_id   INTEGER PRIMARY KEY,
    contact_email TEXT NOT NULL UNIQUE,
    contact_name  TEXT NOT NULL,           -- most recent name on file
    contact_phone TEXT NOT NULL            -- most recent phone on file
);

DROP TABLE IF EXISTS DimMarketingChannel;
CREATE TABLE DimMarketingChannel (
    channel_id   INTEGER PRIMARY KEY,
    channel_name TEXT NOT NULL UNIQUE CHECK (
        channel_name IN ('organic', 'direct', 'referral', 'paid_search', 'paid_social', 'email')
    ),
    channel_type TEXT NOT NULL CHECK (channel_type IN ('paid', 'unpaid'))
);

-- Portability notes:
--   * SQLite has no native ENUM type — CHECK constraints stand in for it.
--     On Postgres these would become a proper ENUM type or a lookup table.
--   * BOOLEAN in SQLite is stored as INTEGER 0/1 — this is transparent to
--     pandas/SQLAlchemy and to Postgres, which has a native BOOLEAN type.