"""
Exports every warehouse table to CSV for import into Power BI Desktop.

Power BI Desktop has no built-in SQLite connector, and installing/
configuring a third-party ODBC driver just to point Power BI at a
single-user, file-based database adds real friction for very little
benefit here — see powerbi/README.md for the full reasoning, including
the ODBC alternative for anyone who wants a live connection instead.

This exports the star schema as-is (dimension and fact tables only, not
the reporting views — Power BI's own measures/relationships do that job
inside the model), so the Kimball structure built in sql/schema/ carries
straight through into the Power BI relationship diagram.

Run directly (after build_warehouse.py):
    python -m src.warehouse.export_for_powerbi
"""

import sqlite3

import pandas as pd

from src.generation import config

DB_PATH = config.WAREHOUSE_DIR / "ascent_analytics.db"
EXPORT_DIR = config.PROJECT_ROOT / "powerbi" / "data_export"

TABLES = [
    "DimDate", "DimRegion", "DimGuide", "DimRoute", "DimCustomer", "DimMarketingChannel",
    "FactBookings", "FactPayments", "FactReviews", "FactEquipmentHire", "FactMarketing",
    "FactWebsiteAnalytics", "FactWeather",
]

# A handful of the reporting views (sql/views/01_reporting_views.sql) are
# worth exporting too, as pre-aggregated summary tables. Recomputing
# customer lifetime value or guide performance from scratch in DAX is
# possible but needlessly complex when the SQL already does it cleanly —
# this is a normal hybrid SQL+DAX pattern, not a shortcut. These load into
# Power BI as standalone tables (not related to the star schema), used
# directly in visuals rather than driving further DAX.
VIEWS_TO_EXPORT = {
    "vw_customer_summary": "Summary_CustomerLTV.csv",
    "vw_guide_performance": "Summary_GuidePerformance.csv",
    "vw_route_performance": "Summary_RoutePerformance.csv",
}


def main():
    if not DB_PATH.exists():
        raise FileNotFoundError(f"{DB_PATH} not found — run `python -m src.warehouse.build_warehouse` first.")

    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    try:
        for table in TABLES:
            df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
            out_path = EXPORT_DIR / f"{table}.csv"
            df.to_csv(out_path, index=False)
            print(f"Exported {len(df):,} rows -> {out_path}")

        existing_views = {
            row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'view'").fetchall()
        }
        for view_name, filename in VIEWS_TO_EXPORT.items():
            if view_name not in existing_views:
                print(f"[!] Skipping {view_name} -> not found — run `python -m src.warehouse.apply_views` first.")
                continue
            df = pd.read_sql_query(f"SELECT * FROM {view_name}", conn)
            out_path = EXPORT_DIR / filename
            df.to_csv(out_path, index=False)
            print(f"Exported {len(df):,} rows -> {out_path}")
    finally:
        conn.close()

    print(f"\nExport complete -> {EXPORT_DIR}")
    print("Next: open Power BI Desktop and follow powerbi/README.md.")


if __name__ == "__main__":
    main()