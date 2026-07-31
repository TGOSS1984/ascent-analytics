"""Sanity tests for the reference data generator.

These aren't data-quality tests (that's the cleaning pipeline's job) —
they just confirm the generator produces the right shape of raw output
deterministically, so a broken generator fails CI immediately.
"""

from src.generation import config
from src.generation.generate_reference_data import (
    generate_guides,
    generate_regions,
    generate_routes,
)
import random
import numpy as np


def _rngs():
    return random.Random(config.RANDOM_SEED), np.random.default_rng(config.RANDOM_SEED)


def test_regions_count_and_columns():
    rng, _ = _rngs()
    df = generate_regions(rng)
    assert len(df) == len(config.REGIONS)
    assert {"region_id", "region_name_raw"}.issubset(df.columns)


def test_guides_have_expected_columns():
    rng, np_rng = _rngs()
    df = generate_guides(rng, np_rng)
    expected = {
        "guide_id", "first_name_raw", "last_name_raw", "qualifications_raw",
        "years_experience", "languages_raw", "employment_type",
        "day_rate_gbp_raw", "primary_region_raw", "active",
    }
    assert expected.issubset(df.columns)
    # duplicate injection should only ever grow the row count
    assert len(df) >= config.GUIDE_COUNT


def test_routes_cover_every_seeded_region():
    rng, np_rng = _rngs()
    df = generate_routes(rng, np_rng)
    seeded_regions = set(config.ROUTE_SEED_DATA.keys())
    generated_regions = set(df["region_name_raw"].str.strip().str.title())
    assert seeded_regions.issubset(generated_regions)


def test_generation_is_deterministic():
    rng1, np_rng1 = _rngs()
    rng2, np_rng2 = _rngs()
    df1 = generate_guides(rng1, np_rng1)
    df2 = generate_guides(rng2, np_rng2)
    assert df1.equals(df2)