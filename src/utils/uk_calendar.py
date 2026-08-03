"""
UK calendar helpers shared between the data generator (to bias booking
dates toward realistic demand spikes) and the warehouse builder (to
expose the same dates as DimDate columns for analysis in Power BI).

Bank holiday rules are for England & Wales, which is a reasonable
simplification for a UK-wide synthetic dataset — Scotland's bank holidays
differ slightly (e.g. St Andrew's Day, different August holiday timing),
but modelling that distinction wasn't judged worth the added complexity
here. Documented as a known simplification.
"""

from datetime import date, timedelta

from dateutil.easter import easter


def _substitute_if_weekend(d: date, taken: set) -> date:
    """UK bank holidays that fall on a weekend are observed on the next
    available weekday. Nudges forward a day at a time to avoid colliding
    with a holiday already placed (e.g. Christmas Day substitute landing
    on the same day as Boxing Day's substitute)."""
    if d.weekday() == 5:  # Saturday
        d = d + timedelta(days=2)
    elif d.weekday() == 6:  # Sunday
        d = d + timedelta(days=1)
    while d in taken:
        d = d + timedelta(days=1)
    return d


def _nth_weekday(year: int, month: int, weekday: int, n: int) -> date:
    """The nth occurrence of `weekday` (Monday=0) in a given month."""
    d = date(year, month, 1)
    offset = (weekday - d.weekday()) % 7
    d = d + timedelta(days=offset + 7 * (n - 1))
    return d


def _last_weekday(year: int, month: int, weekday: int) -> date:
    """The last occurrence of `weekday` (Monday=0) in a given month."""
    if month == 12:
        next_month_first = date(year + 1, 1, 1)
    else:
        next_month_first = date(year, month + 1, 1)
    d = next_month_first - timedelta(days=1)
    offset = (d.weekday() - weekday) % 7
    return d - timedelta(days=offset)


def get_uk_bank_holidays(year: int) -> set:
    """Returns the set of England & Wales bank holiday dates for a given
    year."""
    holidays = set()

    new_years_day = _substitute_if_weekend(date(year, 1, 1), holidays)
    holidays.add(new_years_day)

    easter_sunday = easter(year)
    holidays.add(easter_sunday - timedelta(days=2))  # Good Friday
    holidays.add(easter_sunday + timedelta(days=1))  # Easter Monday

    holidays.add(_nth_weekday(year, 5, 0, 1))  # Early May bank holiday
    holidays.add(_last_weekday(year, 5, 0))  # Spring bank holiday
    holidays.add(_last_weekday(year, 8, 0))  # Summer bank holiday

    christmas_day = _substitute_if_weekend(date(year, 12, 25), holidays)
    holidays.add(christmas_day)
    boxing_day = _substitute_if_weekend(date(year, 12, 26), holidays)
    holidays.add(boxing_day)

    return holidays


def get_uk_bank_holidays_range(start_year: int, end_year: int) -> set:
    """Bank holidays across an inclusive range of years."""
    holidays = set()
    for year in range(start_year, end_year + 1):
        holidays |= get_uk_bank_holidays(year)
    return holidays


def is_summer_holiday(d: date) -> bool:
    """Approximates the English school summer holiday window. Real dates
    vary by 1-2 weeks depending on region and year — not worth modelling
    precisely for this dataset, so a fixed window is used consistently
    across all years."""
    return (d.month == 7 and d.day >= 20) or (d.month == 8)