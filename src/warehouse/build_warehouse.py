"""
Builds the Ascent Analytics SQL warehouse: creates the star schema (via
sql/schema/*.sql) in a fresh SQLite database, then loads it from the
cleaned CSVs in data/cleaned/.

Run directly (after both cleaning pipeline stages have been run):
    python -m src.warehouse.build_warehouse
"""

import sqlite3

import pandas as pd

from src.generation import config

SCHEMA_DIR = config.PROJECT_ROOT / "sql" / "schema"
DB_PATH = config.WAREHOUSE_DIR / "ascent_analytics.db"


# ---------------------------------------------------------------------------
# Schema creation
# ---------------------------------------------------------------------------

def create_schema(conn: sqlite3.Connection):
    for filename in ["01_dimensions.sql", "02_facts.sql", "03_indexes.sql"]:
        sql = (SCHEMA_DIR / filename).read_text()
        conn.executescript(sql)
    conn.commit()


# ---------------------------------------------------------------------------
# Dimension builders
# ---------------------------------------------------------------------------

CALENDAR_SEASON_BY_MONTH = {
    12: "Winter", 1: "Winter", 2: "Winter",
    3: "Spring", 4: "Spring", 5: "Spring",
    6: "Summer", 7: "Summer", 8: "Summer",
    9: "Autumn", 10: "Autumn", 11: "Autumn",
}


def build_dim_date(min_date, max_date) -> pd.DataFrame:
    dates = pd.date_range(min_date, max_date, freq="D")
    df = pd.DataFrame({"full_date": dates})
    df["date_id"] = df["full_date"].dt.strftime("%Y%m%d").astype(int)
    df["day"] = df["full_date"].dt.day
    df["month"] = df["full_date"].dt.month
    df["month_name"] = df["full_date"].dt.strftime("%B")
    df["quarter"] = df["full_date"].dt.quarter
    df["year"] = df["full_date"].dt.year
    df["day_of_week"] = df["full_date"].dt.dayofweek
    df["day_name"] = df["full_date"].dt.strftime("%A")
    df["is_weekend"] = df["day_of_week"].isin([5, 6])
    df["calendar_season"] = df["month"].map(CALENDAR_SEASON_BY_MONTH)
    return df[
        ["date_id", "full_date", "day", "month", "month_name", "quarter", "year",
         "day_of_week", "day_name", "is_weekend", "calendar_season"]
    ]


def build_dim_region(regions_clean: pd.DataFrame) -> pd.DataFrame:
    return regions_clean[["region_id", "name", "slug"]].copy()


def build_dim_guide(guides_clean: pd.DataFrame, dim_region: pd.DataFrame) -> pd.DataFrame:
    df = guides_clean.merge(
        dim_region[["region_id", "name"]].rename(columns={"name": "primary_region"}),
        on="primary_region", how="left",
    )
    df["full_name"] = df["first_name"] + " " + df["last_name"]
    df = df.rename(columns={"region_id": "primary_region_id"})
    return df[
        ["guide_id", "first_name", "last_name", "full_name", "qualifications", "years_experience",
         "languages", "employment_type", "day_rate_gbp", "primary_region_id", "active"]
    ]


def build_dim_route(routes_clean: pd.DataFrame, dim_region: pd.DataFrame) -> pd.DataFrame:
    df = routes_clean.merge(
        dim_region[["region_id", "name"]].rename(columns={"name": "region"}),
        on="region", how="left",
    )
    return df[
        ["route_id", "name", "region_id", "difficulty", "distance_km", "duration_hours",
         "mountain_height_m", "elevation_gain_m", "is_featured", "active",
         "trailhead_lat", "trailhead_lon"]
    ]


def build_dim_customer(bookings_clean: pd.DataFrame) -> pd.DataFrame:
    df = bookings_clean.copy()
    df["email_key"] = df["contact_email"].fillna("").str.lower().str.strip()
    df = df.sort_values("created_at")
    latest = (
        df.groupby("email_key")
        .agg(contact_name=("contact_name", "last"), contact_phone=("contact_phone", "last"))
        .reset_index()
    )
    latest = latest[latest["email_key"] != ""].reset_index(drop=True)
    latest.insert(0, "customer_id", range(1, len(latest) + 1))
    return latest.rename(columns={"email_key": "contact_email"})


def build_dim_marketing_channel() -> pd.DataFrame:
    rows = []
    for i, (channel, (_, cpa, _, _)) in enumerate(config.MARKETING_CHANNELS.items(), start=1):
        rows.append(
            {"channel_id": i, "channel_name": channel, "channel_type": "paid" if cpa > 0 else "unpaid"}
        )
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Fact builders
# ---------------------------------------------------------------------------

def build_fact_bookings(bookings_clean, tours_clean, routes_clean, dim_region, dim_customer,
                         dim_marketing_channel, attribution_clean):
    df = bookings_clean.merge(tours_clean, on="tour_id", how="left", suffixes=("", "_tour"))
    df = df.merge(routes_clean[["route_id", "region"]], on="route_id", how="left")
    df = df.merge(dim_region[["region_id", "name"]].rename(columns={"name": "region"}), on="region", how="left")

    df["email_key"] = df["contact_email"].fillna("").str.lower().str.strip()
    df = df.merge(
        dim_customer[["customer_id", "contact_email"]].rename(columns={"contact_email": "email_key"}),
        on="email_key", how="left",
    )

    df = df.merge(attribution_clean, on="booking_id", how="left")
    df = df.merge(
        dim_marketing_channel[["channel_id", "channel_name"]].rename(columns={"channel_name": "channel"}),
        on="channel", how="left",
    )

    df["created_at"] = pd.to_datetime(df["created_at"])
    df["date"] = pd.to_datetime(df["date"])
    df["tour_date_id"] = df["date"].dt.strftime("%Y%m%d").astype(int)
    df["created_date_id"] = df["created_at"].dt.strftime("%Y%m%d").astype(int)
    df["lead_time_days"] = (df["date"] - df["created_at"].dt.normalize()).dt.days

    out = df[
        [
            "booking_id", "booking_reference", "tour_id", "customer_id", "route_id", "guide_id",
            "region_id", "channel_id", "tour_date_id", "created_date_id", "season", "status",
            "party_size", "total_price", "lead_time_days", "contact_email_invalid",
        ]
    ].copy()
    out["guide_id"] = out["guide_id"].astype("Int64")
    out["channel_id"] = out["channel_id"].astype("Int64")
    return out


def build_fact_payments(payments_clean):
    df = payments_clean.copy()
    df["paid_at"] = pd.to_datetime(df["paid_at"], errors="coerce")
    df["refunded_at"] = pd.to_datetime(df["refunded_at"], errors="coerce")
    df["paid_date_id"] = df["paid_at"].dt.strftime("%Y%m%d")
    df["refunded_date_id"] = df["refunded_at"].dt.strftime("%Y%m%d")
    df["paid_date_id"] = df["paid_date_id"].where(df["paid_date_id"].notna(), None)
    df["refunded_date_id"] = df["refunded_date_id"].where(df["refunded_date_id"].notna(), None)

    out = df[["payment_id", "booking_id", "amount", "currency", "status", "paid_date_id", "refunded_date_id"]]
    return out


def build_fact_reviews(reviews_clean, bookings_fact, bookings_clean_with_route_guide):
    df = reviews_clean.merge(
        bookings_clean_with_route_guide[["booking_id", "customer_id", "route_id", "guide_id"]],
        on="booking_id", how="left",
    )
    return df[
        ["booking_id", "customer_id", "route_id", "guide_id", "overall_rating", "guide_rating",
         "route_rating", "safety_rating", "value_rating", "comment_length", "would_recommend"]
    ]


def build_fact_equipment_hire(equipment_clean, bookings_fact):
    df = equipment_clean.merge(bookings_fact[["booking_id", "customer_id"]], on="booking_id", how="left")
    return df[
        ["booking_id", "customer_id", "boots", "waterproofs", "poles", "helmet", "ice_axe", "crampons", "hire_revenue"]
    ]


def build_fact_marketing(marketing_clean, dim_marketing_channel):
    df = marketing_clean.merge(
        dim_marketing_channel[["channel_id", "channel_name"]].rename(columns={"channel_name": "channel"}),
        on="channel", how="left",
    )
    df["month"] = pd.to_datetime(df["month"])
    df["month_date_id"] = df["month"].dt.strftime("%Y%m%d").astype(int)
    df.insert(0, "marketing_id", range(1, len(df) + 1))
    return df[["marketing_id", "campaign", "channel_id", "month_date_id", "spend", "clicks", "impressions", "conversions", "revenue"]]


def build_fact_website_analytics(website_clean, dim_marketing_channel):
    df = website_clean.copy()
    df["week_starting"] = pd.to_datetime(df["week_starting"])
    df["week_date_id"] = df["week_starting"].dt.strftime("%Y%m%d").astype(int)
    df = df.merge(
        dim_marketing_channel[["channel_id", "channel_name"]].rename(columns={"channel_name": "traffic_source"}),
        on="traffic_source", how="left",
    )
    df.insert(0, "website_analytics_id", range(1, len(df) + 1))
    return df[
        ["website_analytics_id", "week_date_id", "channel_id", "device", "sessions", "users",
         "bounce_rate", "conversion_rate", "browser", "country"]
    ]


def build_fact_weather(weather_clean, dim_region, dim_date):
    df = weather_clean.copy()
    df["date"] = pd.to_datetime(df["date"])
    df["date_id"] = df["date"].dt.strftime("%Y%m%d").astype(int)
    df = df.merge(dim_region[["region_id", "name"]].rename(columns={"name": "region"}), on="region", how="left")
    df.insert(0, "weather_id", range(1, len(df) + 1))
    return df[
        ["weather_id", "date_id", "region_id", "temperature_c", "rain_mm", "wind_speed_kmh",
         "visibility_km", "snow_depth_cm", "storm_warning"]
    ]


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    cleaned = config.CLEANED_DATA_DIR

    regions_clean = pd.read_csv(cleaned / "regions_cleaned.csv")
    guides_clean = pd.read_csv(cleaned / "guides_cleaned.csv")
    routes_clean = pd.read_csv(cleaned / "routes_cleaned.csv")
    tours_clean = pd.read_csv(cleaned / "scheduled_tours_cleaned.csv", parse_dates=["date"])
    bookings_clean = pd.read_csv(cleaned / "bookings_cleaned.csv", parse_dates=["created_at"])
    payments_clean = pd.read_csv(cleaned / "payments_cleaned.csv")
    reviews_clean = pd.read_csv(cleaned / "reviews_cleaned.csv")
    weather_clean = pd.read_csv(cleaned / "weather_cleaned.csv")
    attribution_clean = pd.read_csv(cleaned / "booking_attribution_cleaned.csv")
    marketing_clean = pd.read_csv(cleaned / "marketing_cleaned.csv")
    website_clean = pd.read_csv(cleaned / "website_analytics_cleaned.csv")
    equipment_clean = pd.read_csv(cleaned / "equipment_hire_cleaned.csv")

    all_dates = pd.concat(
        [
            tours_clean["date"], bookings_clean["created_at"].dt.normalize(),
            pd.to_datetime(weather_clean["date"]), pd.to_datetime(marketing_clean["month"]),
            pd.to_datetime(website_clean["week_starting"]),
            pd.to_datetime(payments_clean["paid_at"], errors="coerce").dropna(),
            pd.to_datetime(payments_clean["refunded_at"], errors="coerce").dropna(),
        ]
    )

    dim_date = build_dim_date(all_dates.min().normalize(), all_dates.max().normalize())
    dim_region = build_dim_region(regions_clean)
    dim_guide = build_dim_guide(guides_clean, dim_region)
    dim_route = build_dim_route(routes_clean, dim_region)
    dim_customer = build_dim_customer(bookings_clean)
    dim_marketing_channel = build_dim_marketing_channel()

    fact_bookings = build_fact_bookings(
        bookings_clean, tours_clean, routes_clean, dim_region, dim_customer, dim_marketing_channel, attribution_clean
    )

    # small helper frame reused by FactReviews for route/guide/customer lookups
    bookings_with_route_guide = fact_bookings[["booking_id", "customer_id", "route_id", "guide_id"]]

    fact_payments = build_fact_payments(payments_clean)
    fact_reviews = build_fact_reviews(reviews_clean, fact_bookings, bookings_with_route_guide)
    fact_equipment = build_fact_equipment_hire(equipment_clean, fact_bookings)
    fact_marketing = build_fact_marketing(marketing_clean, dim_marketing_channel)
    fact_website = build_fact_website_analytics(website_clean, dim_marketing_channel)
    fact_weather = build_fact_weather(weather_clean, dim_region, dim_date)

    config.WAREHOUSE_DIR.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = sqlite3.connect(DB_PATH)
    try:
        create_schema(conn)

        load_order = [
            ("DimDate", dim_date), ("DimRegion", dim_region), ("DimGuide", dim_guide),
            ("DimRoute", dim_route), ("DimCustomer", dim_customer), ("DimMarketingChannel", dim_marketing_channel),
            ("FactBookings", fact_bookings), ("FactPayments", fact_payments), ("FactReviews", fact_reviews),
            ("FactEquipmentHire", fact_equipment), ("FactMarketing", fact_marketing),
            ("FactWebsiteAnalytics", fact_website), ("FactWeather", fact_weather),
        ]
        for table_name, df in load_order:
            df.to_sql(table_name, conn, if_exists="append", index=False)
            print(f"Loaded {len(df):,} rows -> {table_name}")

        conn.commit()
    finally:
        conn.close()

    print(f"\nWarehouse built at {DB_PATH}")


if __name__ == "__main__":
    main()