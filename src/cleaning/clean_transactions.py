"""Cleaning rules for the transactional core: ScheduledTour, Booking,
Payment. These depend on the already-cleaned Route/Guide tables for
referential integrity checks."""

import pandas as pd

from src.cleaning.quality_log import QualityLog
from src.cleaning.utils import clean_email, completeness, dedupe, normalize_text, parse_currency


def clean_scheduled_tours(raw_df, routes_clean, log: QualityLog):
    log.log_row_count("ScheduledTour", "raw", len(raw_df))

    df = raw_df.copy()
    df, n_removed = dedupe(df, subset="tour_id")
    if n_removed:
        log.log_metric("ScheduledTour", "duplicates_removed", n_removed)

    df["date"] = pd.to_datetime(df["date"])
    df["season"] = df["season"].str.strip().str.lower()
    df["start_time"] = df["start_time_raw"].str.strip()
    df["price_pp"] = df["price_pp_raw"].apply(parse_currency)
    df["max_group_size"] = df["max_group_size"].astype(int)
    df["status"] = df["status_raw"].str.strip().str.lower()
    df["guide_id"] = df["guide_id"].astype("Int64")  # nullable integer

    invalid_price = df["price_pp"] <= 0
    if invalid_price.any():
        log.log_metric("ScheduledTour", "invalid_price_rows", int(invalid_price.sum()))

    orphan_routes = ~df["route_id"].isin(routes_clean["route_id"])
    if orphan_routes.any():
        log.log_metric("ScheduledTour", "orphan_route_references", int(orphan_routes.sum()))

    df = df[
        ["tour_id", "route_id", "guide_id", "date", "season", "start_time", "price_pp", "max_group_size", "status"]
    ]

    log.log_row_count("ScheduledTour", "cleaned", len(df))
    log.log_metric("ScheduledTour", "completeness", completeness(df, ["date", "season", "status"]))
    return df


def clean_bookings(raw_df, tours_clean, log: QualityLog):
    log.log_row_count("Booking", "raw", len(raw_df))

    df = raw_df.copy()
    df, n_removed = dedupe(df, subset="booking_reference")
    if n_removed:
        log.log_metric("Booking", "duplicate_booking_references_removed", n_removed)

    df["contact_name"] = df["contact_name_raw"].apply(normalize_text)

    emails, invalid_flags = zip(*df["contact_email_raw"].apply(clean_email))
    df["contact_email"] = emails
    df["contact_email_invalid"] = invalid_flags
    n_repaired = (df["contact_email_raw"].astype(str).str.contains(" at ") & ~pd.Series(invalid_flags)).sum()
    if n_repaired:
        log.log_metric("Booking", "malformed_emails_repaired", int(n_repaired), "' at ' -> '@' pattern")
    n_invalid_email = sum(invalid_flags)
    if n_invalid_email:
        log.log_metric("Booking", "malformed_emails_unrepaired", int(n_invalid_email), "flagged via contact_email_invalid")

    df["contact_phone"] = df["contact_phone_raw"].str.strip()
    df["emergency_contact"] = df["emergency_contact_raw"].apply(normalize_text)
    df["notes"] = df["notes_raw"]
    df["status"] = df["status_raw"].str.strip().str.lower()
    df["total_price"] = df["total_price_raw"].apply(parse_currency)
    df["created_at"] = pd.to_datetime(df["created_at"])
    df["archived_at"] = pd.to_datetime(df["archived_at"], errors="coerce")
    df["party_size"] = df["party_size"].astype(int)

    out_of_range_party = ~df["party_size"].between(1, 3)
    if out_of_range_party.any():
        log.log_metric("Booking", "party_size_out_of_range", int(out_of_range_party.sum()))

    orphan_tours = ~df["tour_id"].isin(tours_clean["tour_id"])
    if orphan_tours.any():
        log.log_metric("Booking", "orphan_tour_references", int(orphan_tours.sum()))

    df = df[
        [
            "booking_id", "tour_id", "booking_reference", "party_size", "contact_name", "contact_email",
            "contact_email_invalid", "contact_phone", "emergency_contact", "notes", "status", "total_price",
            "created_at", "archived_at",
        ]
    ]

    log.log_row_count("Booking", "cleaned", len(df))
    log.log_metric("Booking", "completeness", completeness(df, ["contact_name", "contact_email", "status"]))
    return df


def clean_payments(raw_df, bookings_clean, log: QualityLog):
    log.log_row_count("Payment", "raw", len(raw_df))

    df = raw_df.copy()
    df, n_removed = dedupe(df, subset="payment_id")
    if n_removed:
        log.log_metric("Payment", "duplicates_removed", n_removed)

    n_lowercase_currency = (df["currency_raw"].str.strip() == "gbp").sum()
    if n_lowercase_currency:
        log.log_metric("Payment", "currency_casing_fixed", int(n_lowercase_currency))
    df["currency"] = df["currency_raw"].str.strip().str.upper()

    df["amount"] = df["amount_raw"].apply(parse_currency)
    df["status"] = df["status_raw"].str.strip().str.lower()
    df["paid_at"] = pd.to_datetime(df["paid_at"], errors="coerce")
    df["refunded_at"] = pd.to_datetime(df["refunded_at"], errors="coerce")

    orphan_bookings = ~df["booking_id"].isin(bookings_clean["booking_id"])
    if orphan_bookings.any():
        log.log_metric("Payment", "orphan_booking_references", int(orphan_bookings.sum()))

    df = df[
        [
            "payment_id", "booking_id", "stripe_payment_intent_id", "stripe_checkout_session_id",
            "stripe_refund_id", "amount", "currency", "status", "paid_at", "refunded_at",
        ]
    ]

    log.log_row_count("Payment", "cleaned", len(df))
    log.log_metric("Payment", "completeness", completeness(df, ["amount", "currency", "status"]))
    return df