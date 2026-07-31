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


# ---------------------------------------------------------------------------
# Extension-layer schemas
# ---------------------------------------------------------------------------

ReviewSchema = DataFrameSchema(
    {
        "booking_id": Column(int, unique=True),
        "overall_rating": Column(pa.Int64, Check.in_range(1, 5), nullable=True),
        "guide_rating": Column(pa.Int64, Check.in_range(1, 5), nullable=True),
        "route_rating": Column(pa.Int64, Check.in_range(1, 5), nullable=True),
        "safety_rating": Column(pa.Int64, Check.in_range(1, 5), nullable=True),
        "value_rating": Column(pa.Int64, Check.in_range(1, 5), nullable=True),
        "comment_length": Column(int, Check.ge(0)),
        "would_recommend": Column(bool, nullable=True),
    }
)

WeatherSchema = DataFrameSchema(
    {
        "date": Column(pa.DateTime),
        "region": Column(str, nullable=False),
        "temperature_c": Column(float),
        "rain_mm": Column(float, Check.ge(0)),
        "wind_speed_kmh": Column(float, Check.ge(0)),
        "visibility_km": Column(float, Check.ge(0)),
        "snow_depth_cm": Column(float, Check.ge(0)),
        "storm_warning": Column(bool),
    }
)

BookingAttributionSchema = DataFrameSchema(
    {
        "booking_id": Column(int, unique=True),
        "channel": Column(
            str, Check.isin(["organic", "direct", "referral", "paid_search", "paid_social", "email"])
        ),
    }
)

MarketingSchema = DataFrameSchema(
    {
        "campaign": Column(str, nullable=False),
        "channel": Column(str, nullable=False),
        "month": Column(pa.DateTime),
        "spend": Column(float, Check.ge(0)),
        "clicks": Column(int, Check.ge(0)),
        "impressions": Column(int, Check.ge(0)),
        "conversions": Column(int, Check.ge(0)),
        "revenue": Column(float, Check.ge(0)),
    }
)

WebsiteAnalyticsSchema = DataFrameSchema(
    {
        "week_starting": Column(pa.DateTime),
        "traffic_source": Column(str, nullable=False),
        "device": Column(str, Check.isin(["mobile", "desktop", "tablet"])),
        "sessions": Column(int, Check.ge(0)),
        "users": Column(int, Check.ge(0)),
        "bounce_rate": Column(float, Check.in_range(0, 1)),
        "conversion_rate": Column(float, Check.in_range(0, 1)),
        "browser": Column(str, nullable=False),
        "country": Column(str, nullable=False),
    }
)

EquipmentHireSchema = DataFrameSchema(
    {
        "booking_id": Column(int, unique=True),
        "boots": Column(bool, nullable=True),
        "waterproofs": Column(bool, nullable=True),
        "poles": Column(bool, nullable=True),
        "helmet": Column(bool, nullable=True),
        "ice_axe": Column(bool, nullable=True),
        "crampons": Column(bool, nullable=True),
        "hire_revenue": Column(float, Check.ge(0)),
    }
)

EXTENSION_SCHEMAS = {
    "Review": ReviewSchema,
    "Weather": WeatherSchema,
    "BookingAttribution": BookingAttributionSchema,
    "Marketing": MarketingSchema,
    "WebsiteAnalytics": WebsiteAnalyticsSchema,
    "EquipmentHire": EquipmentHireSchema,
}