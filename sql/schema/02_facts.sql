-- Fact tables for the Ascent Analytics warehouse.
-- Run after 01_dimensions.sql — every foreign key here references a table
-- created there.

PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS FactBookings;
CREATE TABLE FactBookings (
    booking_id         INTEGER PRIMARY KEY,
    booking_reference   TEXT NOT NULL UNIQUE,
    tour_id             INTEGER NOT NULL,      -- degenerate: identifies the ScheduledTour event, no DimTour table (see architecture notes)
    customer_id          INTEGER NOT NULL REFERENCES DimCustomer(customer_id),
    route_id             INTEGER NOT NULL REFERENCES DimRoute(route_id),
    guide_id             INTEGER REFERENCES DimGuide(guide_id),           -- nullable: some tours had no guide assigned
    region_id            INTEGER NOT NULL REFERENCES DimRegion(region_id), -- denormalised from route for query convenience
    channel_id           INTEGER REFERENCES DimMarketingChannel(channel_id),
    tour_date_id          INTEGER NOT NULL REFERENCES DimDate(date_id),
    created_date_id       INTEGER NOT NULL REFERENCES DimDate(date_id),
    season                TEXT NOT NULL CHECK (season IN ('winter', 'summer')),  -- degenerate dimension
    status                TEXT NOT NULL CHECK (status IN ('pending', 'confirmed', 'cancelled', 'amended')),
    party_size            INTEGER NOT NULL CHECK (party_size BETWEEN 1 AND 3),
    list_price             REAL NOT NULL,        -- undiscounted price (price_pp x party_size)
    discount_pct            REAL NOT NULL,        -- 0 if no discount applied
    discount_applied         BOOLEAN NOT NULL,
    total_price           REAL NOT NULL,        -- actual price paid (list_price x (1 - discount_pct))
    lead_time_days        INTEGER NOT NULL,
    contact_email_invalid BOOLEAN NOT NULL
);

DROP TABLE IF EXISTS FactPayments;
CREATE TABLE FactPayments (
    payment_id       INTEGER PRIMARY KEY,
    booking_id        INTEGER NOT NULL UNIQUE REFERENCES FactBookings(booking_id),
    amount            REAL NOT NULL,
    currency          TEXT NOT NULL CHECK (currency = 'GBP'),
    status            TEXT NOT NULL CHECK (status IN ('pending', 'paid', 'refund_pending', 'refunded', 'failed')),
    paid_date_id      INTEGER REFERENCES DimDate(date_id),
    refunded_date_id  INTEGER REFERENCES DimDate(date_id)
);

DROP TABLE IF EXISTS FactReviews;
CREATE TABLE FactReviews (
    booking_id      INTEGER PRIMARY KEY REFERENCES FactBookings(booking_id),
    customer_id     INTEGER NOT NULL REFERENCES DimCustomer(customer_id),
    route_id        INTEGER NOT NULL REFERENCES DimRoute(route_id),
    guide_id        INTEGER REFERENCES DimGuide(guide_id),
    overall_rating  INTEGER CHECK (overall_rating BETWEEN 1 AND 5),
    guide_rating    INTEGER CHECK (guide_rating BETWEEN 1 AND 5),
    route_rating    INTEGER CHECK (route_rating BETWEEN 1 AND 5),
    safety_rating   INTEGER CHECK (safety_rating BETWEEN 1 AND 5),
    value_rating    INTEGER CHECK (value_rating BETWEEN 1 AND 5),
    comment_length  INTEGER NOT NULL,
    would_recommend BOOLEAN
);

DROP TABLE IF EXISTS FactEquipmentHire;
CREATE TABLE FactEquipmentHire (
    booking_id    INTEGER PRIMARY KEY REFERENCES FactBookings(booking_id),
    customer_id   INTEGER NOT NULL REFERENCES DimCustomer(customer_id),
    boots         BOOLEAN NOT NULL,
    waterproofs   BOOLEAN NOT NULL,
    poles         BOOLEAN NOT NULL,
    helmet        BOOLEAN NOT NULL,
    ice_axe       BOOLEAN NOT NULL,
    crampons      BOOLEAN NOT NULL,
    hire_revenue  REAL NOT NULL
);

DROP TABLE IF EXISTS FactMarketing;
CREATE TABLE FactMarketing (
    marketing_id  INTEGER PRIMARY KEY,
    campaign      TEXT NOT NULL,
    channel_id    INTEGER NOT NULL REFERENCES DimMarketingChannel(channel_id),
    month_date_id INTEGER NOT NULL REFERENCES DimDate(date_id),  -- first-of-month
    spend         REAL NOT NULL,
    clicks        INTEGER NOT NULL,
    impressions   INTEGER NOT NULL,
    conversions   INTEGER NOT NULL,
    revenue       REAL NOT NULL
);

DROP TABLE IF EXISTS FactWebsiteAnalytics;
CREATE TABLE FactWebsiteAnalytics (
    website_analytics_id INTEGER PRIMARY KEY,
    week_date_id          INTEGER NOT NULL REFERENCES DimDate(date_id),  -- week starting (Monday)
    channel_id             INTEGER NOT NULL REFERENCES DimMarketingChannel(channel_id),
    device                 TEXT NOT NULL CHECK (device IN ('mobile', 'desktop', 'tablet')),
    sessions                INTEGER NOT NULL,
    users                   INTEGER NOT NULL,
    bounce_rate             REAL NOT NULL,
    conversion_rate         REAL NOT NULL,
    browser                 TEXT NOT NULL,
    country                 TEXT NOT NULL
);

DROP TABLE IF EXISTS FactWeather;
CREATE TABLE FactWeather (
    weather_id      INTEGER PRIMARY KEY,
    date_id         INTEGER NOT NULL REFERENCES DimDate(date_id),
    region_id       INTEGER NOT NULL REFERENCES DimRegion(region_id),
    temperature_c   REAL NOT NULL,
    rain_mm         REAL NOT NULL,
    wind_speed_kmh  REAL NOT NULL,
    visibility_km   REAL NOT NULL,
    snow_depth_cm   REAL NOT NULL,
    storm_warning   BOOLEAN NOT NULL,
    UNIQUE (date_id, region_id)
);