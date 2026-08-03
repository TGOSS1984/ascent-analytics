"""
Generate raw (intentionally messy) transactional data: ScheduledTour,
Booking, Payment.

Depends on the reference data logic in generate_reference_data.py — this
script regenerates the same reference dataframes in-memory (same seed, so
byte-for-byte identical to what was written to data/raw/ in the previous
step) rather than re-parsing the messy CSVs, so FK relationships are
guaranteed valid. A light amount of internal normalisation is applied to
the raw fields purely so this script can reason about them (e.g. matching
a guide to a route's region) — that is NOT a substitute for the real
cleaning pipeline, which operates on the CSVs as written to disk.

Run directly:
    python -m src.generation.generate_transactions
"""

import calendar
import random
import uuid

import numpy as np
import pandas as pd
from faker import Faker

from src.generation import config
from src.generation.generate_reference_data import (
    generate_guides,
    generate_regions,
    generate_routes,
)
from src.utils import messiness, uk_calendar


# ---------------------------------------------------------------------------
# Reference data setup
# ---------------------------------------------------------------------------

def build_reference_lookups():
    rng = random.Random(config.RANDOM_SEED)
    np_rng = np.random.default_rng(config.RANDOM_SEED)

    guides_df = generate_guides(rng, np_rng).drop_duplicates(subset="guide_id").reset_index(drop=True)
    routes_df = generate_routes(rng, np_rng).drop_duplicates(subset="route_id").reset_index(drop=True)

    guides_df["primary_region_clean"] = guides_df["primary_region_raw"].str.strip().str.title()
    routes_df["region_clean"] = routes_df["region_name_raw"].str.strip().str.title()
    routes_df["difficulty_clean"] = routes_df["difficulty_raw"].str.strip().str.lower()
    routes_df["duration_hours"] = routes_df["duration_hours"].astype(float)

    return guides_df, routes_df


def assign_guide_tenure(guides_df: pd.DataFrame, np_rng: np.random.Generator) -> pd.DataFrame:
    """Give every guide a company join date, and a leave date for guides
    already flagged inactive, so tour assignment respects who was actually
    available on a given date rather than treating the whole roster as
    available for the entire 7-year window."""
    start = pd.Timestamp(config.START_DATE)
    end = pd.Timestamp(config.END_DATE)
    total_days = (end - start).days

    join_dates, leave_dates = [], []
    for active in guides_df["active"]:
        join_frac = np_rng.beta(1.5, 4)  # skewed toward joining early
        join_date = start + pd.Timedelta(days=int(join_frac * total_days * 0.7))
        join_dates.append(join_date)

        if not active:
            remaining_days = max((end - join_date).days, 1)
            leave_frac = np_rng.uniform(0.3, 0.95)
            leave_dates.append(join_date + pd.Timedelta(days=int(remaining_days * leave_frac)))
        else:
            leave_dates.append(pd.NaT)

    guides_df["company_joined_at"] = join_dates
    guides_df["company_left_at"] = leave_dates
    return guides_df


# ---------------------------------------------------------------------------
# ScheduledTour generation
# ---------------------------------------------------------------------------

def _pick_month(season: str, rng: random.Random) -> int:
    weights = config.SEASON_MONTH_WEIGHTS[season]
    return rng.choices(list(weights.keys()), weights=list(weights.values()))[0]


def _day_weight(ts: pd.Timestamp, bank_holidays: set) -> float:
    """Relative likelihood of a tour landing on this date. Multiplicative
    factors compound naturally — a bank holiday that falls on a weekend
    (or the Friday/Monday of a long weekend) gets both boosts, producing
    exactly the kind of spike a real leisure guiding business would see."""
    weight = 1.0
    if ts.dayofweek in (4, 5, 6):  # Fri, Sat, Sun
        weight *= 2.2
    if ts.date() in bank_holidays:
        weight *= 3.0
    if uk_calendar.is_summer_holiday(ts.date()):
        weight *= 1.6
    return weight


def _pick_day(year: int, month: int, rng: random.Random, bank_holidays: set) -> int:
    days_in_month = calendar.monthrange(year, month)[1]
    candidates = [pd.Timestamp(year=year, month=month, day=d) for d in range(1, days_in_month + 1)]
    weights = [_day_weight(ts, bank_holidays) for ts in candidates]
    chosen = rng.choices(candidates, weights=weights)[0]
    return chosen.day


def generate_scheduled_tours(guides_df, routes_df, rng, np_rng):
    rows = []
    tour_id = 1
    route_weights = np.where(routes_df["is_featured"], 2.0, 1.0)
    bank_holidays = uk_calendar.get_uk_bank_holidays_range(
        pd.Timestamp(config.START_DATE).year, pd.Timestamp(config.END_DATE).year + 1
    )

    for year, n_tours in config.ANNUAL_TOUR_COUNTS.items():
        for _ in range(n_tours):
            route = routes_df.sample(1, weights=route_weights, random_state=np_rng.integers(0, 2**31)).iloc[0]

            season = rng.choices(config.SEASONS, weights=[0.45, 0.55])[0]
            month = _pick_month(season, rng)
            day = _pick_day(year, month, rng, bank_holidays)
            date = pd.Timestamp(year=year, month=month, day=day)

            candidates = guides_df[
                (guides_df["primary_region_clean"] == route["region_clean"])
                & (guides_df["company_joined_at"] <= date)
                & (guides_df["company_left_at"].isna() | (guides_df["company_left_at"] >= date))
            ]
            if candidates.empty:
                # fall back to any guide available that day, regardless of
                # primary region — a guide occasionally covers another area
                candidates = guides_df[
                    (guides_df["company_joined_at"] <= date)
                    & (guides_df["company_left_at"].isna() | (guides_df["company_left_at"] >= date))
                ]
            guide_id = None
            if not candidates.empty:
                guide_id = int(candidates.sample(1, random_state=np_rng.integers(0, 2**31))["guide_id"].iloc[0])

            difficulty = route["difficulty_clean"]
            diff_uplift = {"moderate": 15, "hard": 35, "advanced": 60}[difficulty]
            base_price = 55 + diff_uplift + float(route["duration_hours"]) * 7
            year_inflation = 1 + 0.035 * (year - 2019)
            noise = max(np_rng.normal(1.0, 0.08), 0.6)
            price_pp = round(base_price * year_inflation * noise, 2)

            max_group_size = 3
            if difficulty == "advanced" and rng.random() < 0.4:
                max_group_size = 2

            # ~4-10% of tours fall through for reasons outside the
            # operator's control (guide illness, severe weather, access
            # closures) — rate scales with difficulty since harder routes
            # run in more exposed, weather-sensitive terrain. Finalised in
            # the post-processing pass below.
            ops_cancel_rate = config.DIFFICULTY_OPS_CANCEL_RATE.get(difficulty, 0.06)
            weather_or_ops_cancelled = rng.random() < ops_cancel_rate

            rows.append(
                {
                    "tour_id": tour_id,
                    "route_id": int(route["route_id"]),
                    "guide_id": guide_id,
                    "date": date,
                    "season": season,
                    "start_time_raw": rng.choice(config.START_TIMES),
                    "price_pp_raw": messiness.scramble_currency(price_pp, rng),
                    "max_group_size": max_group_size,
                    "ops_cancelled": weather_or_ops_cancelled,
                }
            )
            tour_id += 1

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Booking + Payment generation
# ---------------------------------------------------------------------------

def _lead_time_days(rng: random.Random, np_rng: np.random.Generator) -> int:
    days = int(np_rng.lognormal(mean=3.2, sigma=0.9))
    return min(max(days, 1), 400)


def _booking_status(rng: random.Random, created_at: pd.Timestamp, dataset_end: pd.Timestamp) -> str:
    days_from_end = (dataset_end - created_at).days
    if days_from_end < 14 and rng.random() < 0.5:
        return "pending"
    return rng.choices(
        ["confirmed", "cancelled", "amended"],
        weights=[0.84, 0.12, 0.04],
    )[0]


def _payment_status(rng: random.Random, booking_status: str) -> str:
    if booking_status == "pending":
        return "pending"
    if booking_status in ("confirmed", "amended"):
        return rng.choices(["paid", "pending"], weights=[0.94, 0.06])[0]
    # cancelled
    return rng.choices(
        ["refunded", "refund_pending", "failed", "pending"],
        weights=[0.62, 0.14, 0.14, 0.10],
    )[0]


def generate_bookings_and_payments(tours_df, guides_df, rng, np_rng, faker: Faker):
    booking_rows = []
    payment_rows = []
    tour_booked_spaces = {}
    tour_had_any_booking = set()

    discount_tendency_by_guide = dict(zip(guides_df["guide_id"], guides_df["discount_tendency_pct"]))

    booking_id = 1
    payment_id = 1
    dataset_end = pd.Timestamp(config.END_DATE)

    for tour in tours_df.itertuples(index=False):
        if tour.ops_cancelled:
            # tour cancelled outright — still simulate the (now unlucky)
            # people who *had* booked before the cancellation went out
            n_attempts = rng.choices([0, 1, 2], weights=[0.50, 0.35, 0.15])[0]
        else:
            n_attempts = rng.choices([0, 1, 2], weights=[0.08, 0.32, 0.60])[0]

        remaining_capacity = tour.max_group_size
        for _ in range(n_attempts):
            if remaining_capacity <= 0:
                break
            party_size = rng.choices(
                [s for s in (1, 2, 3) if s <= remaining_capacity],
                weights=[w for s, w in zip((1, 2, 3), (0.45, 0.40, 0.15)) if s <= remaining_capacity],
            )[0]
            remaining_capacity -= party_size

            lead_days = _lead_time_days(rng, np_rng)
            created_at = tour.date - pd.Timedelta(days=lead_days)
            if created_at < pd.Timestamp(config.START_DATE):
                created_at = pd.Timestamp(config.START_DATE)

            if tour.ops_cancelled:
                status = "cancelled"
            else:
                status = _booking_status(rng, created_at, dataset_end)

            list_price = round(float(str(tour.price_pp_raw).replace("£", "").replace("GBP", "").strip() if isinstance(tour.price_pp_raw, str) else tour.price_pp_raw) * party_size, 2)

            # Discount, correlated with the assigned guide's individual
            # tendency — a guide with a higher tendency both discounts a
            # larger share of their bookings AND discounts more deeply
            # when they do. Unguided tours never get a discount (nobody
            # to apply one).
            guide_tendency = discount_tendency_by_guide.get(tour.guide_id, 0.0) if pd.notna(tour.guide_id) else 0.0
            discount_probability = min(guide_tendency * 3.0, 0.6)
            discount_applied = guide_tendency > 0 and rng.random() < discount_probability
            if discount_applied:
                discount_pct = round(float(np.clip(np_rng.normal(guide_tendency, guide_tendency * 0.3), 0.01, 0.30)), 4)
            else:
                discount_pct = 0.0
            total_price = round(list_price * (1 - discount_pct), 2)

            name = faker.name()
            email = faker.email()
            if rng.random() < 0.03:
                email = email.replace("@", " at ")  # malformed entry
            phone = faker.phone_number()

            archived_at = None
            if status == "cancelled" and (dataset_end - created_at).days > 365 and rng.random() < 0.5:
                archived_at = created_at + pd.Timedelta(days=rng.randint(30, 200))

            booking_rows.append(
                {
                    "booking_id": booking_id,
                    "tour_id": tour.tour_id,
                    "booking_reference": uuid.uuid4().hex[:10].upper(),
                    "party_size": party_size,
                    "contact_name_raw": messiness.mangle_casing(name, rng),
                    "contact_email_raw": email,
                    "contact_phone_raw": phone,
                    "emergency_contact_raw": faker.name() if rng.random() < 0.7 else None,
                    "notes_raw": faker.sentence() if rng.random() < 0.1 else None,
                    "status_raw": messiness.mangle_casing(status, rng),
                    "list_price_raw": messiness.scramble_currency(list_price, rng),
                    "discount_pct": discount_pct,
                    "discount_applied": discount_applied,
                    "total_price_raw": messiness.scramble_currency(total_price, rng),
                    "created_at": created_at,
                    "archived_at": archived_at,
                }
            )

            payment_status = _payment_status(rng, status)
            paid_at = created_at + pd.Timedelta(hours=rng.randint(0, 48)) if payment_status == "paid" else None
            refunded_at = (
                created_at + pd.Timedelta(days=rng.randint(1, 20)) if payment_status == "refunded" else None
            )

            payment_rows.append(
                {
                    "payment_id": payment_id,
                    "booking_id": booking_id,
                    "stripe_payment_intent_id": f"pi_{uuid.uuid4().hex[:16]}",
                    "stripe_checkout_session_id": f"cs_{uuid.uuid4().hex[:16]}",
                    "stripe_refund_id": f"re_{uuid.uuid4().hex[:16]}" if payment_status == "refunded" else "",
                    "amount_raw": messiness.scramble_currency(total_price, rng),
                    "currency_raw": rng.choice(["GBP", "GBP", "GBP", "gbp"]),
                    "status_raw": messiness.mangle_casing(payment_status, rng),
                    "paid_at": paid_at,
                    "refunded_at": refunded_at,
                }
            )

            tour_had_any_booking.add(tour.tour_id)
            tour_booked_spaces[tour.tour_id] = tour_booked_spaces.get(tour.tour_id, 0) + party_size
            booking_id += 1
            payment_id += 1

    bookings_df = pd.DataFrame(booking_rows)
    payments_df = pd.DataFrame(payment_rows)
    return bookings_df, payments_df, tour_booked_spaces, tour_had_any_booking


def finalise_tour_status(tours_df, tour_booked_spaces, tour_had_any_booking, rng):
    statuses = []
    for tour in tours_df.itertuples(index=False):
        if tour.ops_cancelled:
            statuses.append("cancelled")
            continue
        booked = tour_booked_spaces.get(tour.tour_id, 0)
        if booked == 0:
            # published tour that never got a single booking — small
            # operators typically pull these rather than run them empty
            statuses.append("cancelled" if rng.random() < 0.7 else "open")
        elif booked >= tour.max_group_size:
            statuses.append("full")
        else:
            statuses.append("open")
    tours_df["status_raw"] = [messiness.mangle_casing(s, rng) for s in statuses]
    return tours_df


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    rng = random.Random(config.RANDOM_SEED + 100)
    np_rng = np.random.default_rng(config.RANDOM_SEED + 100)
    faker = Faker("en_GB")
    Faker.seed(config.RANDOM_SEED)

    config.RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    guides_df, routes_df = build_reference_lookups()
    guides_df = assign_guide_tenure(guides_df, np_rng)

    tours_df = generate_scheduled_tours(guides_df, routes_df, rng, np_rng)
    bookings_df, payments_df, tour_booked_spaces, tour_had_any_booking = generate_bookings_and_payments(
        tours_df, guides_df, rng, np_rng, faker
    )
    tours_df = finalise_tour_status(tours_df, tour_booked_spaces, tour_had_any_booking, rng)
    tours_df = tours_df.drop(columns=["ops_cancelled"])

    tours_path = config.RAW_DATA_DIR / "scheduled_tours_raw.csv"
    bookings_path = config.RAW_DATA_DIR / "bookings_raw.csv"
    payments_path = config.RAW_DATA_DIR / "payments_raw.csv"

    tours_df.to_csv(tours_path, index=False)
    bookings_df.to_csv(bookings_path, index=False)
    payments_df.to_csv(payments_path, index=False)

    print(f"Wrote {len(tours_df):,} scheduled tours -> {tours_path}")
    print(f"Wrote {len(bookings_df):,} bookings -> {bookings_path}")
    print(f"Wrote {len(payments_df):,} payments -> {payments_path}")


if __name__ == "__main__":
    main()