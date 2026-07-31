"""Tests for the Power BI CSV export."""

import pandas as pd
import pytest

from src.generation import config
from src.warehouse.export_for_powerbi import TABLES, VIEWS_TO_EXPORT

EXPORT_DIR = config.PROJECT_ROOT / "powerbi" / "data_export"


def _require_export():
    if not any(EXPORT_DIR.glob("*.csv")):
        pytest.skip(f"No CSVs found in {EXPORT_DIR} — run `python -m src.warehouse.export_for_powerbi` first.")


def test_every_star_schema_table_exported_with_rows():
    _require_export()
    for table in TABLES:
        path = EXPORT_DIR / f"{table}.csv"
        assert path.exists(), f"{path} missing"
        df = pd.read_csv(path)
        assert len(df) > 0, f"{table}.csv is empty"


def test_summary_views_exported_with_rows():
    _require_export()
    for view_name, filename in VIEWS_TO_EXPORT.items():
        path = EXPORT_DIR / filename
        if not path.exists():
            pytest.skip(f"{filename} not exported — run apply_views.py before export_for_powerbi.py")
        df = pd.read_csv(path)
        assert len(df) > 0, f"{filename} is empty"


def test_factbookings_export_has_expected_columns():
    _require_export()
    df = pd.read_csv(EXPORT_DIR / "FactBookings.csv")
    expected = {
        "booking_id", "customer_id", "route_id", "guide_id", "region_id",
        "tour_date_id", "created_date_id", "status", "total_price",
    }
    assert expected.issubset(df.columns)