"""
Generate raw (intentionally messy) reference/dimension data:
Region, Guide, Route.

These are the "slow-changing" entities that scheduled tours and bookings
will reference in the next generation step, so they're built first.

Run directly:
    python -m src.generation.generate_reference_data
"""

import random

import numpy as np
import pandas as pd

from src.generation import config
from src.utils import messiness


def generate_regions(rng: random.Random) -> pd.DataFrame:
    rows = []
    for i, name in enumerate(config.REGIONS, start=1):
        raw_name = messiness.mangle_casing(name, rng)
        rows.append(
            {
                "region_id": i,
                "region_name_raw": raw_name,
            }
        )
    return pd.DataFrame(rows)


def generate_guides(rng: random.Random, np_rng: np.random.Generator) -> pd.DataFrame:
    first_names = [
        "James", "Sarah", "Tom", "Emily", "Owen", "Lucy", "Rhys", "Katie",
        "Callum", "Megan", "Fraser", "Anna", "Dylan", "Bethan", "Hamish",
        "Chloe", "Iestyn", "Isla", "Finlay", "Gwen", "Angus", "Rowan",
    ]
    last_names = [
        "Griffiths", "MacLeod", "Evans", "Fraser", "Hughes", "Campbell",
        "Pritchard", "Stewart", "Owen", "Munro", "Davies", "Ross",
        "Lloyd", "Grant", "Parry", "Robertson", "Vaughan", "Wallace",
        "Rees", "Sinclair", "Morgan", "Cameron",
    ]

    rows = []
    for i in range(1, config.GUIDE_COUNT + 1):
        first = first_names[(i - 1) % len(first_names)]
        last = last_names[(i - 1) % len(last_names)]

        years_experience = int(np_rng.integers(1, 25))
        n_quals = int(np_rng.integers(1, 4))
        quals = rng.sample(config.QUALIFICATIONS_POOL, k=n_quals)
        n_langs = int(np_rng.integers(1, 3))
        langs = rng.sample(config.LANGUAGES_POOL, k=n_langs)
        employment_type = rng.choice(config.EMPLOYMENT_TYPES)
        day_rate = round(float(np_rng.normal(180, 35)), 2)
        day_rate = max(day_rate, 90.0)
        primary_region = rng.choice(config.REGIONS)

        # active = False for guides who have left partway through the
        # 7-year window, to give the cleaning/warehouse layer something
        # real to reason about (guide utilisation shouldn't count them
        # after they've left).
        active = rng.random() > 0.15

        rows.append(
            {
                "guide_id": i,
                "first_name_raw": messiness.mangle_casing(first, rng),
                "last_name_raw": messiness.mangle_casing(last, rng),
                "qualifications_raw": messiness.maybe_null(
                    "; ".join(quals), 0.03, rng
                ),
                "years_experience": years_experience,
                "languages_raw": "; ".join(langs),
                "employment_type": employment_type,
                "day_rate_gbp_raw": messiness.scramble_currency(day_rate, rng),
                "primary_region_raw": messiness.mangle_casing(primary_region, rng),
                "active": active,
            }
        )

    df = pd.DataFrame(rows)
    # a couple of accidental duplicate guide submissions
    df = messiness.duplicate_rows(df, rate=0.02, rng_seed=config.RANDOM_SEED)
    return df


def generate_routes(rng: random.Random, np_rng: np.random.Generator) -> pd.DataFrame:
    rows = []
    route_id = 1
    for region, routes in config.ROUTE_SEED_DATA.items():
        for name, difficulty, distance_km, duration_hours, height_m, elevation_m in routes:
            is_featured = rng.random() < 0.2
            active = rng.random() > 0.05  # a handful of retired routes

            # occasionally store distance as a messy string with units
            distance_val = distance_km
            if rng.random() < 0.03:
                distance_val = f"{distance_km} km"

            elevation_val = messiness.maybe_null(elevation_m, 0.02, rng)

            rows.append(
                {
                    "route_id": route_id,
                    "route_name_raw": messiness.mangle_casing(name, rng),
                    "region_name_raw": messiness.mangle_casing(region, rng),
                    "difficulty_raw": messiness.mangle_casing(difficulty, rng),
                    "distance_km_raw": distance_val,
                    "duration_hours": duration_hours,
                    "mountain_height_m": height_m,
                    "elevation_gain_m_raw": elevation_val,
                    "is_featured": is_featured,
                    "active": active,
                }
            )
            route_id += 1

    df = pd.DataFrame(rows)
    df = messiness.duplicate_rows(df, rate=0.01, rng_seed=config.RANDOM_SEED + 1)
    return df


def main():
    rng = random.Random(config.RANDOM_SEED)
    np_rng = np.random.default_rng(config.RANDOM_SEED)

    config.RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    regions_df = generate_regions(rng)
    guides_df = generate_guides(rng, np_rng)
    routes_df = generate_routes(rng, np_rng)

    regions_path = config.RAW_DATA_DIR / "regions_raw.csv"
    guides_path = config.RAW_DATA_DIR / "guides_raw.csv"
    routes_path = config.RAW_DATA_DIR / "routes_raw.csv"

    regions_df.to_csv(regions_path, index=False)
    guides_df.to_csv(guides_path, index=False)
    routes_df.to_csv(routes_path, index=False)

    print(f"Wrote {len(regions_df)} regions -> {regions_path}")
    print(f"Wrote {len(guides_df)} guides -> {guides_path}")
    print(f"Wrote {len(routes_df)} routes -> {routes_path}")


if __name__ == "__main__":
    main()