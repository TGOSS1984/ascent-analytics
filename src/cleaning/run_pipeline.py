"""
Orchestrates the cleaning pipeline for the core entities: Region, Guide,
Route, ScheduledTour, Booking, Payment.

Reads raw CSVs from data/raw/, applies the cleaning rules in
clean_reference.py and clean_transactions.py, validates the result against
the pandera schemas in schemas.py, writes cleaned CSVs to data/cleaned/,
and writes a data quality log to docs/data_quality/.

Extension-layer cleaning (Review, Weather, Marketing, WebsiteAnalytics,
EquipmentHire) is handled separately — see the next pipeline step.

Run directly (after all three generation scripts have been run):
    python -m src.cleaning.run_pipeline
"""

import pandas as pd
from pandera.errors import SchemaErrors

from src.generation import config
from src.cleaning.clean_reference import clean_guides, clean_regions, clean_routes
from src.cleaning.clean_transactions import clean_bookings, clean_payments, clean_scheduled_tours
from src.cleaning.quality_log import QualityLog
from src.cleaning.schemas import CORE_SCHEMAS


def _validate(name, df, log: QualityLog):
    schema = CORE_SCHEMAS[name]
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
    config.WAREHOUSE_DIR.mkdir(parents=True, exist_ok=True)

    raw = {}
    for filename in [
        "regions_raw.csv", "guides_raw.csv", "routes_raw.csv",
        "scheduled_tours_raw.csv", "bookings_raw.csv", "payments_raw.csv",
    ]:
        path = config.RAW_DATA_DIR / filename
        if not path.exists():
            raise FileNotFoundError(
                f"{path} not found — run the three generation scripts "
                "(generate_reference_data, generate_transactions, generate_extensions) first."
            )
        raw[filename] = pd.read_csv(path)

    regions = clean_regions(raw["regions_raw.csv"], log)
    guides = clean_guides(raw["guides_raw.csv"], log)
    routes = clean_routes(raw["routes_raw.csv"], log)

    tours = clean_scheduled_tours(raw["scheduled_tours_raw.csv"], routes, log)
    bookings = clean_bookings(raw["bookings_raw.csv"], tours, log)
    payments = clean_payments(raw["payments_raw.csv"], bookings, log)

    tables = {
        "Region": regions, "Guide": guides, "Route": routes,
        "ScheduledTour": tours, "Booking": bookings, "Payment": payments,
    }
    for name, df in tables.items():
        _validate(name, df, log)

    filename_map = {
        "Region": "regions_cleaned.csv", "Guide": "guides_cleaned.csv", "Route": "routes_cleaned.csv",
        "ScheduledTour": "scheduled_tours_cleaned.csv", "Booking": "bookings_cleaned.csv",
        "Payment": "payments_cleaned.csv",
    }
    for name, df in tables.items():
        out_path = config.CLEANED_DATA_DIR / filename_map[name]
        df.to_csv(out_path, index=False)
        print(f"Wrote {len(df):,} rows -> {out_path}")

    log_path = config.PROJECT_ROOT / "docs" / "data_quality" / "core_pipeline_log.csv"
    log.save_csv(log_path)
    log.print_summary()
    print(f"\nQuality log written to {log_path}")


if __name__ == "__main__":
    main()