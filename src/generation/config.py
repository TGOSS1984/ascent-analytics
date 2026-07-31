"""
Shared configuration and reference constants for the Ascent Analytics
synthetic data generation pipeline.

Field-level provenance (Core vs Extension) is documented in
docs/data_dictionary/README.md — this module just centralises the values
used across generator scripts so every script draws from the same source
of truth (e.g. two scripts never invent slightly different region lists).
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# Reproducibility
# ---------------------------------------------------------------------------
RANDOM_SEED = 42

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
CLEANED_DATA_DIR = PROJECT_ROOT / "data" / "cleaned"
WAREHOUSE_DIR = PROJECT_ROOT / "data" / "warehouse"

# ---------------------------------------------------------------------------
# Time horizon
# ---------------------------------------------------------------------------
# ~7 years of trading history, targeting ~30,000 bookings overall.
START_DATE = "2019-01-01"
END_DATE = "2025-12-31"
TARGET_BOOKINGS = 30_000

# ---------------------------------------------------------------------------
# Regions [Core] — aligned to routes_app.Region
# ---------------------------------------------------------------------------
REGIONS = [
    "Snowdonia",
    "Lake District",
    "Scottish Highlands",
    "Peak District",
    "Brecon Beacons",
    "Cairngorms",
]

# ---------------------------------------------------------------------------
# Routes [Core] — aligned to routes_app.Route
# ---------------------------------------------------------------------------
# difficulty choices are a closed enum in the real app — do not add "easy"
DIFFICULTIES = ["moderate", "hard", "advanced"]

# Named routes per region, roughly ordered easy -> hard within each region.
# (name, difficulty, distance_km, duration_hours, mountain_height_m, elevation_gain_m)
ROUTE_SEED_DATA = {
    "Snowdonia": [
        ("Snowdon via Llanberis Path", "moderate", 14.5, 6.0, 1085, 975),
        ("Snowdon via Pyg Track", "hard", 12.0, 6.5, 1085, 920),
        ("Snowdon Horseshoe", "advanced", 11.0, 8.5, 1085, 1000),
        ("Tryfan North Ridge", "advanced", 6.5, 6.0, 918, 800),
        ("Cadair Idris via Minffordd Path", "hard", 10.0, 6.0, 893, 890),
        ("Y Garn Circuit", "moderate", 9.5, 5.5, 947, 730),
    ],
    "Lake District": [
        ("Scafell Pike via Corridor Route", "hard", 13.0, 7.0, 978, 900),
        ("Helvellyn via Striding Edge", "advanced", 12.5, 7.5, 950, 780),
        ("Catbells and Derwentwater", "moderate", 7.0, 3.5, 451, 360),
        ("Blencathra via Sharp Edge", "advanced", 9.0, 6.0, 868, 700),
        ("Old Man of Coniston", "moderate", 9.5, 4.5, 803, 620),
        ("Great Gable via Sty Head", "hard", 11.0, 6.5, 899, 810),
    ],
    "Scottish Highlands": [
        ("Ben Nevis via Mountain Track", "hard", 17.0, 8.0, 1345, 1350),
        ("Ben Nevis via CMD Arete", "advanced", 15.0, 9.5, 1345, 1400),
        ("Aonach Eagach Ridge", "advanced", 10.0, 8.0, 967, 1100),
        ("Buachaille Etive Mor", "hard", 11.0, 7.0, 1022, 900),
        ("Ben Lomond via Tourist Path", "moderate", 11.5, 5.5, 974, 950),
        ("Liathach Traverse", "advanced", 12.0, 9.0, 1055, 1150),
    ],
    "Peak District": [
        ("Kinder Scout via Jacob's Ladder", "moderate", 13.0, 5.5, 636, 480),
        ("Mam Tor Ridge Walk", "moderate", 9.0, 4.0, 517, 350),
        ("Bleaklow Circuit", "hard", 15.0, 6.5, 633, 470),
        ("Stanage Edge and Higger Tor", "moderate", 10.5, 4.5, 458, 300),
    ],
    "Brecon Beacons": [
        ("Pen y Fan via Corn Du", "moderate", 8.0, 3.5, 886, 500),
        ("Pen y Fan Horseshoe", "hard", 13.0, 6.0, 886, 750),
        ("Waun Fach", "moderate", 14.0, 6.0, 811, 600),
        ("Fan y Big Ridge", "hard", 12.0, 6.5, 719, 650),
    ],
    "Cairngorms": [
        ("Cairn Gorm via Ptarmigan", "moderate", 10.0, 5.0, 1245, 700),
        ("Ben Macdui via Coire Cas", "hard", 18.0, 9.0, 1309, 950),
        ("Cairngorm 4000s Traverse", "advanced", 26.0, 12.0, 1309, 1600),
        ("Lairig Ghru Crossing", "advanced", 31.0, 13.0, 835, 950),
    ],
}

# ---------------------------------------------------------------------------
# Guides — first/last name, qualifications, active are [Core].
# years_experience, languages, employment_type, day_rate_gbp are [Ext]
# (plausible operational fields the real app doesn't yet capture).
# ---------------------------------------------------------------------------
GUIDE_COUNT = 22

QUALIFICATIONS_POOL = [
    "Mountain Leader (ML)",
    "Winter Mountain Leader (WML)",
    "International Mountain Leader (IML)",
    "Mountaineering Instructor (MIA)",
    "Winter Mountaineering and Climbing Instructor (WMCI)",
    "Rock Climbing Instructor (RCI)",
    "First Aid at Work",
    "Wilderness First Aid",
    "Avalanche Awareness Certificate",
]

LANGUAGES_POOL = ["English", "Welsh", "French", "German", "Spanish", "Gaelic"]

EMPLOYMENT_TYPES = ["employed", "freelance"]

# ---------------------------------------------------------------------------
# Seasons [Core] — closed enum in the real app
# ---------------------------------------------------------------------------
SEASONS = ["winter", "summer"]

# ---------------------------------------------------------------------------
# ScheduledTour volume by year [Core-driven synthetic volume]
# ---------------------------------------------------------------------------
# A realistic growth curve for a small operator, including a COVID-19 dip
# in 2020 and a gradual recovery — this kind of real-world shock is exactly
# the sort of thing a stakeholder would expect an analyst to explain in the
# insight report, not smooth away.
ANNUAL_TOUR_COUNTS = {
    2019: 2400,
    2020: 1300,  # pandemic disruption
    2021: 2000,  # partial recovery
    2022: 3100,
    2023: 3700,
    2024: 4200,
    2025: 4600,
}

# Winter months cluster Nov-Mar, summer months cluster Apr-Oct, with core
# months weighted higher than shoulder months within each season.
SEASON_MONTH_WEIGHTS = {
    "winter": {11: 0.15, 12: 0.25, 1: 0.25, 2: 0.20, 3: 0.15},
    "summer": {4: 0.08, 5: 0.12, 6: 0.18, 7: 0.22, 8: 0.20, 9: 0.13, 10: 0.07},
}

START_TIMES = ["07:00", "07:30", "08:00", "08:30", "09:00", "09:30"]