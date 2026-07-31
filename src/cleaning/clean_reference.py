"""Cleaning rules for the reference/dimension entities: Region, Guide,
Route. Each function takes the raw dataframe (as read from data/raw/) and
the shared QualityLog, and returns a cleaned dataframe ready for the
warehouse — see docs/data_dictionary/README.md for the rule behind each
field."""

import numpy as np

from src.cleaning.quality_log import QualityLog
from src.cleaning.utils import completeness, dedupe, normalize_text


def clean_regions(raw_df, log: QualityLog):
    log.log_row_count("Region", "raw", len(raw_df))

    df = raw_df.copy()
    df, n_removed = dedupe(df, subset="region_id")
    if n_removed:
        log.log_metric("Region", "duplicates_removed", n_removed)

    df["name"] = df["region_name_raw"].apply(normalize_text)
    df["slug"] = df["name"].str.lower().str.replace(" ", "-", regex=False)
    df = df[["region_id", "name", "slug"]]

    log.log_row_count("Region", "cleaned", len(df))
    log.log_metric("Region", "completeness", completeness(df, ["name", "slug"]))
    return df


def clean_guides(raw_df, log: QualityLog):
    log.log_row_count("Guide", "raw", len(raw_df))

    df = raw_df.copy()
    df, n_removed = dedupe(df, subset="guide_id")
    if n_removed:
        log.log_metric("Guide", "duplicates_removed", n_removed, "raw submissions duplicated (~2% injected)")

    df["first_name"] = df["first_name_raw"].apply(normalize_text)
    df["last_name"] = df["last_name_raw"].apply(normalize_text)

    missing_quals = df["qualifications_raw"].isna().sum()
    if missing_quals:
        log.log_metric(
            "Guide", "missing_qualifications", int(missing_quals),
            "flagged, not imputed — a real data gap worth surfacing"
        )
    df["qualifications"] = df["qualifications_raw"].where(df["qualifications_raw"].notna(), None)

    df["years_experience"] = df["years_experience"].astype(int)
    df["languages"] = df["languages_raw"]
    df["employment_type"] = df["employment_type"].str.strip().str.lower()

    df["day_rate_gbp"] = df["day_rate_gbp_raw"].apply(
        lambda v: float(str(v).replace("£", "").replace("GBP", "").replace(",", "").strip())
    )
    n_currency_strings = df["day_rate_gbp_raw"].apply(lambda v: isinstance(v, str)).sum()
    if n_currency_strings:
        log.log_metric("Guide", "currency_strings_parsed", int(n_currency_strings))

    df["primary_region"] = df["primary_region_raw"].apply(normalize_text)
    df["active"] = df["active"].astype(bool)

    df = df[
        [
            "guide_id", "first_name", "last_name", "qualifications", "years_experience",
            "languages", "employment_type", "day_rate_gbp", "primary_region", "active",
        ]
    ]

    log.log_row_count("Guide", "cleaned", len(df))
    log.log_metric("Guide", "completeness", completeness(df, ["first_name", "last_name", "primary_region"]))
    return df


def clean_routes(raw_df, log: QualityLog):
    log.log_row_count("Route", "raw", len(raw_df))

    df = raw_df.copy()
    df, n_removed = dedupe(df, subset="route_id")
    if n_removed:
        log.log_metric("Route", "duplicates_removed", n_removed, "raw submissions duplicated (~1% injected)")

    df["name"] = df["route_name_raw"].apply(normalize_text)
    df["region"] = df["region_name_raw"].apply(normalize_text)
    df["difficulty"] = df["difficulty_raw"].str.strip().str.lower()

    valid_difficulties = {"moderate", "hard", "advanced"}
    invalid = ~df["difficulty"].isin(valid_difficulties)
    if invalid.any():
        log.log_metric("Route", "invalid_difficulty_values", int(invalid.sum()))

    df["distance_km"] = df["distance_km_raw"].apply(
        lambda v: float(str(v).lower().replace("km", "").strip())
    )
    n_distance_strings = df["distance_km_raw"].apply(lambda v: isinstance(v, str)).sum()
    if n_distance_strings:
        log.log_metric("Route", "distance_unit_strings_parsed", int(n_distance_strings))

    df["duration_hours"] = df["duration_hours"].astype(float)
    df["mountain_height_m"] = df["mountain_height_m"].astype(int)

    # elevation_gain_m: impute missing values with the median for routes of
    # the same difficulty tier, and log exactly how many rows were touched
    # so the imputation is auditable rather than silent.
    missing_elevation = df["elevation_gain_m_raw"].isna()
    if missing_elevation.any():
        medians = df.groupby("difficulty")["elevation_gain_m_raw"].transform("median")
        df["elevation_gain_m"] = df["elevation_gain_m_raw"].fillna(medians)
        log.log_metric(
            "Route", "elevation_gain_imputed", int(missing_elevation.sum()),
            "filled with median elevation_gain_m for the route's difficulty tier"
        )
    else:
        df["elevation_gain_m"] = df["elevation_gain_m_raw"]
    df["elevation_gain_m"] = df["elevation_gain_m"].astype(int)

    df["is_featured"] = df["is_featured"].astype(bool)
    df["active"] = df["active"].astype(bool)

    df = df[
        [
            "route_id", "name", "region", "difficulty", "distance_km", "duration_hours",
            "mountain_height_m", "elevation_gain_m", "is_featured", "active",
        ]
    ]

    log.log_row_count("Route", "cleaned", len(df))
    log.log_metric("Route", "completeness", completeness(df, ["name", "region", "difficulty"]))
    return df