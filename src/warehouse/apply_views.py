"""
Applies the reporting views (sql/views/*.sql) to the warehouse database.
Run after build_warehouse.py.

Run directly:
    python -m src.warehouse.apply_views
"""

import sqlite3

from src.generation import config

VIEWS_DIR = config.PROJECT_ROOT / "sql" / "views"
DB_PATH = config.WAREHOUSE_DIR / "ascent_analytics.db"


def main():
    if not DB_PATH.exists():
        raise FileNotFoundError(f"{DB_PATH} not found — run `python -m src.warehouse.build_warehouse` first.")

    conn = sqlite3.connect(DB_PATH)
    try:
        for path in sorted(VIEWS_DIR.glob("*.sql")):
            conn.executescript(path.read_text())
            print(f"Applied {path.name}")
        conn.commit()

        views = conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'view' ORDER BY name"
        ).fetchall()
        print(f"\n{len(views)} views now available: {', '.join(v[0] for v in views)}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()