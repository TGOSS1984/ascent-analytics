"""
Reusable helpers for injecting realistic data quality issues into
otherwise-clean synthetic data.

The point of Ascent Analytics is to demonstrate a cleaning pipeline that
does real work — so raw data is deliberately generated with the kinds of
issues a small operator's spreadsheets and forms would actually produce.
Every function here is documented so the cleaning pipeline (src/cleaning)
can reference exactly what it needs to detect and fix.
"""

import random
import numpy as np
import pandas as pd


def maybe_null(value, probability: float, rng: random.Random):
    """Return None instead of `value` with the given probability."""
    return None if rng.random() < probability else value


def mangle_casing(text: str, rng: random.Random) -> str:
    """Randomly upper/lower/title-case a string to simulate inconsistent
    manual data entry (e.g. 'snowdonia', 'SNOWDONIA', 'Snowdonia')."""
    if text is None:
        return text
    choice = rng.random()
    if choice < 0.15:
        return text.upper()
    if choice < 0.30:
        return text.lower()
    if choice < 0.35:
        return f"  {text}  "  # stray whitespace
    return text


def typo_country_name(country: str, rng: random.Random) -> str:
    """Introduce common real-world inconsistencies in country naming."""
    variants = {
        "United Kingdom": ["UK", "United Kingdom", "U.K.", "Great Britain", "England"],
        "United States": ["USA", "United States", "U.S.A.", "US", "United States of America"],
        "Germany": ["Germany", "Deutschland", "DE"],
        "France": ["France", "FR"],
        "Ireland": ["Ireland", "Republic of Ireland", "IE"],
    }
    if country in variants and rng.random() < 0.4:
        return rng.choice(variants[country])
    return country


def inject_invalid_age(age: int, rng: random.Random) -> int:
    """Occasionally corrupt an age value (data entry slip, e.g. typing an
    extra digit or a birth year instead of an age)."""
    if rng.random() < 0.01:
        return rng.choice([0, -1, 150, 999])
    return age


def duplicate_rows(df: pd.DataFrame, rate: float, rng_seed: int) -> pd.DataFrame:
    """Append exact or near-exact duplicate rows to simulate duplicate
    submissions (e.g. a booking form double-submitted on a slow connection)."""
    rng = np.random.default_rng(rng_seed)
    n_dupes = int(len(df) * rate)
    if n_dupes == 0:
        return df
    dupe_idx = rng.choice(df.index, size=n_dupes, replace=True)
    dupes = df.loc[dupe_idx].copy()
    return pd.concat([df, dupes], ignore_index=True)


def scramble_currency(value: float, rng: random.Random) -> str:
    """Occasionally return a price as a string with currency symbols/commas
    mixed in, simulating inconsistent export formats."""
    if rng.random() < 0.02:
        formats = [f"£{value:,.2f}", f"GBP {value:.2f}", f"{value:.2f} GBP", f"£{value:.0f}"]
        return rng.choice(formats)
    return value


def inject_outlier(value: float, rng: random.Random, multiplier_range=(5, 20)) -> float:
    """Occasionally multiply a numeric value up to create an outlier."""
    if rng.random() < 0.005:
        return round(value * rng.uniform(*multiplier_range), 2)
    return value