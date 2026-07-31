-- Indexes for the Ascent Analytics warehouse.
-- Run after 01_dimensions.sql and 02_facts.sql.
--
-- SQLite automatically indexes PRIMARY KEY and UNIQUE columns, so those
-- aren't repeated here. These target the foreign keys and filter columns
-- that every dashboard query hits: date range, region, status, season.

-- FactBookings — the busiest table, filtered/joined on almost everything
CREATE INDEX IF NOT EXISTS idx_factbookings_tour_date ON FactBookings(tour_date_id);
CREATE INDEX IF NOT EXISTS idx_factbookings_created_date ON FactBookings(created_date_id);
CREATE INDEX IF NOT EXISTS idx_factbookings_customer ON FactBookings(customer_id);
CREATE INDEX IF NOT EXISTS idx_factbookings_route ON FactBookings(route_id);
CREATE INDEX IF NOT EXISTS idx_factbookings_guide ON FactBookings(guide_id);
CREATE INDEX IF NOT EXISTS idx_factbookings_region ON FactBookings(region_id);
CREATE INDEX IF NOT EXISTS idx_factbookings_channel ON FactBookings(channel_id);
CREATE INDEX IF NOT EXISTS idx_factbookings_status ON FactBookings(status);
CREATE INDEX IF NOT EXISTS idx_factbookings_season ON FactBookings(season);

-- FactPayments
CREATE INDEX IF NOT EXISTS idx_factpayments_status ON FactPayments(status);
CREATE INDEX IF NOT EXISTS idx_factpayments_paid_date ON FactPayments(paid_date_id);

-- FactReviews
CREATE INDEX IF NOT EXISTS idx_factreviews_route ON FactReviews(route_id);
CREATE INDEX IF NOT EXISTS idx_factreviews_guide ON FactReviews(guide_id);

-- FactEquipmentHire
CREATE INDEX IF NOT EXISTS idx_factequipment_customer ON FactEquipmentHire(customer_id);

-- FactMarketing
CREATE INDEX IF NOT EXISTS idx_factmarketing_channel ON FactMarketing(channel_id);
CREATE INDEX IF NOT EXISTS idx_factmarketing_month ON FactMarketing(month_date_id);

-- FactWebsiteAnalytics
CREATE INDEX IF NOT EXISTS idx_factwebsite_week ON FactWebsiteAnalytics(week_date_id);
CREATE INDEX IF NOT EXISTS idx_factwebsite_channel ON FactWebsiteAnalytics(channel_id);
CREATE INDEX IF NOT EXISTS idx_factwebsite_device ON FactWebsiteAnalytics(device);

-- FactWeather
CREATE INDEX IF NOT EXISTS idx_factweather_date ON FactWeather(date_id);
CREATE INDEX IF NOT EXISTS idx_factweather_region ON FactWeather(region_id);

-- Dimension lookups by natural key (used during the warehouse load itself)
CREATE INDEX IF NOT EXISTS idx_dimguide_region ON DimGuide(primary_region_id);
CREATE INDEX IF NOT EXISTS idx_dimroute_region ON DimRoute(region_id);