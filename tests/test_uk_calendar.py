"""Tests for the shared UK bank holiday and summer holiday calculator."""

from datetime import date

from src.utils.uk_calendar import get_uk_bank_holidays, get_uk_bank_holidays_range, is_summer_holiday


def test_bank_holidays_count_per_year():
    for year in [2019, 2020, 2021, 2022, 2023, 2024, 2025]:
        holidays = get_uk_bank_holidays(year)
        assert len(holidays) == 8


def test_known_2021_christmas_substitution():
    """2021: Christmas Day (Sat 25th) -> Mon 27th; Boxing Day (Sun 26th) -> Tue 28th.
    A well-documented real case worth pinning as a regression test."""
    holidays = get_uk_bank_holidays(2021)
    assert date(2021, 12, 27) in holidays
    assert date(2021, 12, 28) in holidays
    assert date(2021, 12, 25) not in holidays
    assert date(2021, 12, 26) not in holidays


def test_known_2022_new_years_day_substitution():
    """2022: New Year's Day (Sat 1st) -> Mon 3rd."""
    holidays = get_uk_bank_holidays(2022)
    assert date(2022, 1, 3) in holidays
    assert date(2022, 1, 1) not in holidays


def test_good_friday_and_easter_monday_are_always_weekdays():
    for year in range(2019, 2026):
        holidays = get_uk_bank_holidays(year)
        weekday_names = [d.weekday() for d in holidays]
        # every bank holiday must land on a weekday (0-4), never a weekend
        assert all(w < 5 for w in weekday_names)


def test_range_helper_matches_individual_year_calls():
    combined = get_uk_bank_holidays_range(2020, 2021)
    individual = get_uk_bank_holidays(2020) | get_uk_bank_holidays(2021)
    assert combined == individual


def test_summer_holiday_window():
    assert is_summer_holiday(date(2024, 7, 25)) is True
    assert is_summer_holiday(date(2024, 8, 15)) is True
    assert is_summer_holiday(date(2024, 7, 1)) is False
    assert is_summer_holiday(date(2024, 9, 1)) is False