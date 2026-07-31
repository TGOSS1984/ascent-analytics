"""Tracks data quality metrics as the cleaning pipeline runs, so the
Data Quality Dashboard (see docs/kpi_catalogue) has something real to
report on: row counts by stage, duplicate rates, completeness,
imputation counts, and validation failures — not just a claim that
cleaning happened.
"""

from datetime import datetime, timezone

import pandas as pd


class QualityLog:
    def __init__(self):
        self._records = []
        self.run_started_at = datetime.now(timezone.utc)

    def log_row_count(self, table: str, stage: str, row_count: int, notes: str = ""):
        self._records.append(
            {
                "table": table,
                "metric": "row_count",
                "stage": stage,
                "value": row_count,
                "notes": notes,
            }
        )

    def log_metric(self, table: str, metric: str, value, notes: str = ""):
        self._records.append(
            {
                "table": table,
                "metric": metric,
                "stage": "cleaning",
                "value": value,
                "notes": notes,
            }
        )

    def to_dataframe(self) -> pd.DataFrame:
        df = pd.DataFrame(self._records)
        if df.empty:
            return df
        df.insert(0, "run_started_at", self.run_started_at.isoformat())
        return df

    def save_csv(self, path):
        df = self.to_dataframe()
        df.to_csv(path, index=False)
        return path

    def print_summary(self):
        df = self.to_dataframe()
        if df.empty:
            print("Quality log is empty.")
            return
        row_counts = df[df["metric"] == "row_count"]
        print("\n=== Row counts by stage ===")
        pivot = row_counts.pivot_table(index="table", columns="stage", values="value", aggfunc="first")
        print(pivot.fillna("-"))

        other = df[df["metric"] != "row_count"]
        if not other.empty:
            print("\n=== Other quality metrics ===")
            for row in other.itertuples(index=False):
                note = f" ({row.notes})" if row.notes else ""
                print(f"  {row.table:25s} {row.metric:22s} {row.value}{note}")