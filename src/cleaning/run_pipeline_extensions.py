"""
Orchestrates the cleaning pipeline for the synthetic extension layer:
Review, Weather, Marketing, BookingAttribution, WebsiteAnalytics,
EquipmentHire.

Depends on the already-cleaned core tables (Region, Booking) for
referential integrity checks, so run_pipeline.py (core) must be run first.

Run directly:
    python -m src.cleaning.run_pipeline_extensions
"""

import pandas as pd
from pandera.errors import SchemaErrors

from src.generation import config
from src.cleaning.clean_extensions import (
    clean_booking_attribution,
    clean_equipment_hire,
    clean_marketing,
    clean_reviews,
    clean_website_analytics,
    clean_weather,
)
from src.cleaning.quality_log import QualityLog
from src.cleaning.schemas import EXTENSION_SCHEMAS


def _validate(name, df, log: QualityLog):
    schema = EXTENSION_SCHEMAS[name]
    try:
        schema.validate(df, lazy=True)
        log.log_metric(name, "validation_failures", 0)
    except SchemaErrors as err:
        n_failures = len(err.failure_cases)
        log.log_metric(name, "validation_failures", n_failures, "see console output for details")
        print(f"\n[!] {name} failed validation ({n_failures} failure cases):")
        print(err.failure_cases.head(10))
    return df


def main():
    log = QualityLog()
    config.CLEANED_DATA_DIR.mkdir(parents=True, exist_ok=True)

    # dependencies from the core cleaning stage
    regions_path = config.CLEANED_DATA_DIR / "regions_cleaned.csv"
    bookings_path = config.CLEANED_DATA_DIR / "bookings_cleaned.csv"
    if not regions_path.exists() or not bookings_path.exists():
        raise FileNotFoundError(
            "Cleaned core tables not found — run `python -m src.cleaning.run_pipeline` first."
        )
    regions_clean = pd.read_csv(regions_path)
    bookings_clean = pd.read_csv(bookings_path)

    raw = {}
    for filename in [
        "reviews_raw.csv", "weather_raw.csv", "booking_attribution_raw.csv",
        "marketing_raw.csv", "website_analytics_raw.csv", "equipment_hire_raw.csv",
    ]:
        path = config.RAW_DATA_DIR / filename
        if not path.exists():
            raise FileNotFoundError(f"{path} not found — run generate_extensions.py first.")
        raw[filename] = pd.read_csv(path)

    reviews = clean_reviews(raw["reviews_raw.csv"], bookings_clean, log)
    weather = clean_weather(raw["weather_raw.csv"], regions_clean, log)
    attribution = clean_booking_attribution(raw["booking_attribution_raw.csv"], bookings_clean, log)
    marketing = clean_marketing(raw["marketing_raw.csv"], log)
    website = clean_website_analytics(raw["website_analytics_raw.csv"], log)
    equipment = clean_equipment_hire(raw["equipment_hire_raw.csv"], bookings_clean, log)

    tables = {
        "Review": reviews, "Weather": weather, "BookingAttribution": attribution,
        "Marketing": marketing, "WebsiteAnalytics": website, "EquipmentHire": equipment,
    }
    for name, df in tables.items():
        _validate(name, df, log)

    filename_map = {
        "Review": "reviews_cleaned.csv", "Weather": "weather_cleaned.csv",
        "BookingAttribution": "booking_attribution_cleaned.csv", "Marketing": "marketing_cleaned.csv",
        "WebsiteAnalytics": "website_analytics_cleaned.csv", "EquipmentHire": "equipment_hire_cleaned.csv",
    }
    for name, df in tables.items():
        out_path = config.CLEANED_DATA_DIR / filename_map[name]
        df.to_csv(out_path, index=False)
        print(f"Wrote {len(df):,} rows -> {out_path}")

    log_path = config.PROJECT_ROOT / "docs" / "data_quality" / "extension_pipeline_log.csv"
    log.save_csv(log_path)
    log.print_summary()
    print(f"\nQuality log written to {log_path}")


if __name__ == "__main__":
    main()