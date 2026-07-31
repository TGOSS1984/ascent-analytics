"""Shared, reusable cleaning helpers used by every cleaning module.

Each function here resolves exactly one class of messiness introduced by
src/utils/messiness.py during generation — see docs/data_dictionary for
the field-by-field mapping of which rule applies where.
"""

import re

import pandas as pd


def normalize_text(value):
    """Strip whitespace and title-case a free-text field (names, regions,
    route names). Returns None for null/empty input rather than 'None'."""
    if pd.isna(value):
        return None
    text = str(value).strip()
    if not text:
        return None
    return text.title()


def normalize_lower(value):
    """Strip whitespace and lowercase a closed-enum field (status,
    difficulty, season, currency)."""
    if pd.isna(value):
        return None
    return str(value).strip().lower()


def parse_currency(value):
    """Parse a numeric or currency-formatted string ('£99.95', 'GBP 99.95',
    '1,133.78', 99.95) into a float. Returns None if unparseable."""
    if pd.isna(value):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value)
    text = text.replace("£", "").replace("GBP", "").replace("gbp", "")
    text = text.replace(",", "").strip()
    try:
        return float(text)
    except ValueError:
        return None


def parse_distance_km(value):
    """Parse a distance value that may be stored as '14.5 km' or a plain
    number."""
    if pd.isna(value):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).lower().replace("km", "").strip()
    try:
        return float(text)
    except ValueError:
        return None


def parse_bool_text(value):
    """Parse a yes/no-style text field (possibly mixed-case) into a real
    boolean. Accepts True/False directly too, since some raw columns are
    already booleans once read back from CSV."""
    if pd.isna(value):
        return None
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in ("true", "yes", "y", "1"):
        return True
    if text in ("false", "no", "n", "0"):
        return False
    return None


EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def clean_email(value):
    """Return (cleaned_email, was_malformed). Attempts to repair the one
    known malformation pattern injected during generation (' at ' in place
    of '@'); anything else that still doesn't match a basic email pattern
    is flagged rather than guessed at."""
    if pd.isna(value):
        return None, True
    text = str(value).strip()
    if " at " in text and "@" not in text:
        repaired = text.replace(" at ", "@", 1)
        if EMAIL_PATTERN.match(repaired):
            return repaired, False
    if EMAIL_PATTERN.match(text):
        return text, False
    return text, True


CANONICAL_COUNTRY_MAP = {
    "uk": "United Kingdom",
    "u.k.": "United Kingdom",
    "great britain": "United Kingdom",
    "england": "United Kingdom",
    "united kingdom": "United Kingdom",
    "usa": "United States",
    "u.s.a.": "United States",
    "us": "United States",
    "united states of america": "United States",
    "united states": "United States",
    "deutschland": "Germany",
    "de": "Germany",
    "germany": "Germany",
    "fr": "France",
    "france": "France",
    "republic of ireland": "Ireland",
    "ie": "Ireland",
    "ireland": "Ireland",
}


def canonicalise_country(value):
    """Map known country-name variants to one canonical form. Returns the
    original (title-cased) value, flagged, if it isn't a recognised
    variant — deliberately not silently dropped or guessed."""
    if pd.isna(value):
        return None, True
    key = str(value).strip().lower()
    if key in CANONICAL_COUNTRY_MAP:
        return CANONICAL_COUNTRY_MAP[key], False
    return str(value).strip().title(), True


def dedupe(df: pd.DataFrame, subset, keep="first"):
    """Drop duplicate rows on `subset`, returning (deduped_df, n_removed)."""
    before = len(df)
    out = df.drop_duplicates(subset=subset, keep=keep).reset_index(drop=True)
    return out, before - len(out)


def completeness(df: pd.DataFrame, columns) -> float:
    """% of non-null cells across the given columns (0-1)."""
    subset = df[columns]
    total_cells = subset.size
    if total_cells == 0:
        return 1.0
    return round(1 - subset.isna().sum().sum() / total_cells, 4)