"""Pandera schemas that validate the *cleaned* core tables before they're
written to data/cleaned/. This is the automated-enforcement counterpart
to the cleaning rules in clean_reference.py / clean_transactions.py — if a
future change to the generator or cleaning logic breaks an assumption
(e.g. a status value outside the closed enum slips through), this fails
loudly instead of silently producing bad warehouse data.
"""

import pandera.pandas as pa
from pandera.pandas import Column, Check, DataFrameSchema

RegionSchema = DataFrameSchema(
    {
        "region_id": Column(int, unique=True),
        "name": Column(str, nullable=False),
        "slug": Column(str, nullable=False),
    }
)

GuideSchema = DataFrameSchema(
    {
        "guide_id": Column(int, unique=True),
        "first_name": Column(str, nullable=False),
        "last_name": Column(str, nullable=False),
        "qualifications": Column(str, nullable=True),
        "years_experience": Column(int, Check.in_range(0, 60)),
        "languages": Column(str, nullable=False),
        "employment_type": Column(str, Check.isin(["employed", "freelance"])),
        "day_rate_gbp": Column(float, Check.gt(0)),
        "primary_region": Column(str, nullable=False),
        "active": Column(bool),
    }
)

RouteSchema = DataFrameSchema(
    {
        "route_id": Column(int, unique=True),
        "name": Column(str, nullable=False),
        "region": Column(str, nullable=False),
        "difficulty": Column(str, Check.isin(["moderate", "hard", "advanced"])),
        "distance_km": Column(float, Check.gt(0)),
        "duration_hours": Column(float, Check.gt(0)),
        "mountain_height_m": Column(int, Check.gt(0)),
        "elevation_gain_m": Column(int, Check.ge(0)),
        "is_featured": Column(bool),
        "active": Column(bool),
    }
)

ScheduledTourSchema = DataFrameSchema(
    {
        "tour_id": Column(int, unique=True),
        "route_id": Column(int),
        "guide_id": Column(pa.Int64, nullable=True),
        "date": Column(pa.DateTime),
        "season": Column(str, Check.isin(["winter", "summer"])),
        "start_time": Column(str, nullable=False),
        "price_pp": Column(float, Check.gt(0)),
        "max_group_size": Column(int, Check.in_range(1, 3)),
        "status": Column(str, Check.isin(["draft", "open", "full", "cancelled"])),
    }
)

BookingSchema = DataFrameSchema(
    {
        "booking_id": Column(int, unique=True),
        "tour_id": Column(int),
        "booking_reference": Column(str, unique=True),
        "party_size": Column(int, Check.in_range(1, 3)),
        "contact_name": Column(str, nullable=False),
        "contact_email": Column(str, nullable=True),
        "contact_email_invalid": Column(bool),
        "contact_phone": Column(str, nullable=False),
        "emergency_contact": Column(str, nullable=True),
        "notes": Column(str, nullable=True),
        "status": Column(str, Check.isin(["pending", "confirmed", "cancelled", "amended"])),
        "total_price": Column(float, Check.gt(0)),
        "created_at": Column(pa.DateTime),
        "archived_at": Column(pa.DateTime, nullable=True),
    }
)

PaymentSchema = DataFrameSchema(
    {
        "payment_id": Column(int, unique=True),
        "booking_id": Column(int, unique=True),
        "stripe_payment_intent_id": Column(str, nullable=False),
        "stripe_checkout_session_id": Column(str, nullable=False),
        "stripe_refund_id": Column(str, nullable=True, coerce=True),
        "amount": Column(float, Check.gt(0)),
        "currency": Column(str, Check.isin(["GBP"])),
        "status": Column(str, Check.isin(["pending", "paid", "refund_pending", "refunded", "failed"])),
        "paid_at": Column(pa.DateTime, nullable=True),
        "refunded_at": Column(pa.DateTime, nullable=True),
    }
)


CORE_SCHEMAS = {
    "Region": RegionSchema,
    "Guide": GuideSchema,
    "Route": RouteSchema,
    "ScheduledTour": ScheduledTourSchema,
    "Booking": BookingSchema,
    "Payment": PaymentSchema,
}