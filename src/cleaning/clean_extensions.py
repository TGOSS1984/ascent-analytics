"""Cleaning rules for the synthetic extension layer: Review, Weather,
Marketing (+ booking attribution), WebsiteAnalytics, EquipmentHire.

Depends on the already-cleaned core tables (Region, Booking) for
referential integrity checks."""

import pandas as pd

from src.cleaning.quality_log import QualityLog
from src.cleaning.utils import (
    canonicalise_country,
    completeness,
    dedupe,
    normalize_text,
    parse_bool_text,
    parse_currency,
)
from src.generation import config


def clean_reviews(raw_df, bookings_clean, log: QualityLog):
    log.log_row_count("Review", "raw", len(raw_df))

    df = raw_df.copy()
    df, n_removed = dedupe(df, subset="booking_id")
    if n_removed:
        log.log_metric("Review", "duplicates_removed", n_removed)

    rating_cols = ["overall_rating", "guide_rating", "route_rating", "safety_rating", "value_rating"]
    for col in rating_cols:
        missing = df[col].isna().sum()
        if missing:
            log.log_metric("Review", f"missing_{col}", int(missing), "left null — not imputed on a 1-5 scale")
        df[col] = df[col].astype("Int64")

    out_of_range = pd.concat([~df[c].between(1, 5) & df[c].notna() for c in rating_cols], axis=1).any(axis=1)
    if out_of_range.any():
        log.log_metric("Review", "ratings_out_of_range", int(out_of_range.sum()))

    df["would_recommend"] = df["would_recommend_raw"].apply(parse_bool_text)
    df["comment_length"] = df["comment_length"].astype(int)

    orphans = ~df["booking_id"].isin(bookings_clean["booking_id"])
    if orphans.any():
        log.log_metric("Review", "orphan_booking_references", int(orphans.sum()))

    df = df[["booking_id"] + rating_cols + ["comment_length", "would_recommend"]]

    log.log_row_count("Review", "cleaned", len(df))
    log.log_metric("Review", "completeness", completeness(df, rating_cols))
    return df


def clean_weather(raw_df, regions_clean, log: QualityLog):
    log.log_row_count("Weather", "raw", len(raw_df))

    df = raw_df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df["region"] = df["region_raw"].apply(normalize_text)

    df, n_removed = dedupe(df, subset=["date", "region"])
    if n_removed:
        log.log_metric("Weather", "duplicates_removed", n_removed)

    invalid_region = ~df["region"].isin(regions_clean["name"])
    if invalid_region.any():
        log.log_metric("Weather", "unrecognised_region", int(invalid_region.sum()))

    for col in ["temperature_c", "rain_mm", "wind_speed_kmh", "visibility_km", "snow_depth_cm"]:
        df[col] = df[col].astype(float)
    df["storm_warning"] = df["storm_warning"].astype(bool)

    negative_rain = df["rain_mm"] < 0
    if negative_rain.any():
        log.log_metric("Weather", "negative_rain_values", int(negative_rain.sum()))

    df = df[["date", "region", "temperature_c", "rain_mm", "wind_speed_kmh", "visibility_km", "snow_depth_cm", "storm_warning"]]

    log.log_row_count("Weather", "cleaned", len(df))
    log.log_metric("Weather", "completeness", completeness(df, ["date", "region", "temperature_c"]))
    return df


def clean_booking_attribution(raw_df, bookings_clean, log: QualityLog):
    log.log_row_count("BookingAttribution", "raw", len(raw_df))

    df = raw_df.copy()
    df, n_removed = dedupe(df, subset="booking_id")
    if n_removed:
        log.log_metric("BookingAttribution", "duplicates_removed", n_removed)

    df["channel"] = df["channel_raw"].str.strip().str.lower()
    valid_channels = set(config.MARKETING_CHANNELS.keys())
    invalid = ~df["channel"].isin(valid_channels)
    if invalid.any():
        log.log_metric("BookingAttribution", "invalid_channel_values", int(invalid.sum()))

    orphans = ~df["booking_id"].isin(bookings_clean["booking_id"])
    if orphans.any():
        log.log_metric("BookingAttribution", "orphan_booking_references", int(orphans.sum()))

    df = df[["booking_id", "channel"]]

    log.log_row_count("BookingAttribution", "cleaned", len(df))
    log.log_metric("BookingAttribution", "completeness", completeness(df, ["channel"]))
    return df


def clean_marketing(raw_df, log: QualityLog):
    log.log_row_count("Marketing", "raw", len(raw_df))

    df = raw_df.copy()
    df["campaign"] = df["campaign_raw"].apply(normalize_text)
    df["channel"] = df["channel_raw"].str.strip().str.lower()
    df["month"] = pd.to_datetime(df["year_month"].astype(str) + "-01")
    df["spend"] = df["spend_raw"].apply(parse_currency)
    df["revenue"] = df["revenue_raw"].apply(parse_currency)
    df["clicks"] = df["clicks"].astype(int)
    df["impressions"] = df["impressions"].astype(int)
    df["conversions"] = df["conversions"].astype(int)

    negative_spend = df["spend"] < 0
    if negative_spend.any():
        log.log_metric("Marketing", "negative_spend_rows", int(negative_spend.sum()))

    df = df[["campaign", "channel", "month", "spend", "clicks", "impressions", "conversions", "revenue"]]

    log.log_row_count("Marketing", "cleaned", len(df))
    log.log_metric("Marketing", "completeness", completeness(df, ["campaign", "channel", "month"]))
    return df


def clean_website_analytics(raw_df, log: QualityLog):
    log.log_row_count("WebsiteAnalytics", "raw", len(raw_df))

    df = raw_df.copy()
    df["week_starting"] = pd.to_datetime(df["week_starting"])
    df["traffic_source"] = df["traffic_source_raw"].str.strip().str.lower()
    df["device"] = df["device_raw"].str.strip().str.lower()
    df["sessions"] = df["sessions"].astype(int)
    df["users"] = df["users"].astype(int)
    df["bounce_rate"] = df["bounce_rate"].clip(0, 1)
    df["conversion_rate"] = df["conversion_rate"].clip(0, 1)
    df["browser"] = df["browser"]

    countries, unmapped_flags = zip(*df["country_raw"].apply(canonicalise_country))
    df["country"] = countries
    n_unmapped = sum(unmapped_flags)
    if n_unmapped:
        log.log_metric("WebsiteAnalytics", "country_unrecognised_variant", int(n_unmapped))
    n_corrected = (df["country_raw"].astype(str).str.strip() != pd.Series(countries)).sum()
    if n_corrected:
        log.log_metric("WebsiteAnalytics", "country_names_standardised", int(n_corrected), "e.g. 'UK'/'U.K.' -> 'United Kingdom'")

    valid_devices = set(config.DEVICES.keys())
    invalid_device = ~df["device"].isin(valid_devices)
    if invalid_device.any():
        log.log_metric("WebsiteAnalytics", "invalid_device_values", int(invalid_device.sum()))

    df = df[
        ["week_starting", "traffic_source", "device", "sessions", "users", "bounce_rate", "conversion_rate", "browser", "country"]
    ]

    log.log_row_count("WebsiteAnalytics", "cleaned", len(df))
    log.log_metric("WebsiteAnalytics", "completeness", completeness(df, ["traffic_source", "device", "country"]))
    return df


EQUIPMENT_ITEMS = ["boots", "waterproofs", "poles", "helmet", "ice_axe", "crampons"]


def clean_equipment_hire(raw_df, bookings_clean, log: QualityLog):
    log.log_row_count("EquipmentHire", "raw", len(raw_df))

    df = raw_df.copy()
    df, n_removed = dedupe(df, subset="booking_id")
    if n_removed:
        log.log_metric("EquipmentHire", "duplicates_removed", n_removed)

    for item in EQUIPMENT_ITEMS:
        df[item] = df[f"{item}_raw"].apply(parse_bool_text)

    df["hire_revenue"] = df["hire_revenue_raw"].apply(parse_currency)

    negative_revenue = df["hire_revenue"] < 0
    if negative_revenue.any():
        log.log_metric("EquipmentHire", "negative_revenue_rows", int(negative_revenue.sum()))

    orphans = ~df["booking_id"].isin(bookings_clean["booking_id"])
    if orphans.any():
        log.log_metric("EquipmentHire", "orphan_booking_references", int(orphans.sum()))

    df = df[["booking_id"] + EQUIPMENT_ITEMS + ["hire_revenue"]]

    log.log_row_count("EquipmentHire", "cleaned", len(df))
    log.log_metric("EquipmentHire", "completeness", completeness(df, EQUIPMENT_ITEMS + ["hire_revenue"]))
    return df