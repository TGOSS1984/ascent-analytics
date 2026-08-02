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
    # (name, difficulty, distance_km, duration_hours, mountain_height_m, elevation_gain_m, trailhead_lat, trailhead_lon)
    # Coordinates are approximate real-world trailhead/start-point locations
    # for the named route — good enough to place a route correctly on a map
    # visual, not survey-grade precision.
    "Snowdonia": [
        ("Snowdon via Llanberis Path", "moderate", 14.5, 6.0, 1085, 975, 53.1201, -4.1174),
        ("Snowdon via Pyg Track", "hard", 12.0, 6.5, 1085, 920, 53.0912, -4.0567),
        ("Snowdon Horseshoe", "advanced", 11.0, 8.5, 1085, 1000, 53.0900, -4.0580),
        ("Tryfan North Ridge", "advanced", 6.5, 6.0, 918, 800, 53.1096, -4.0654),
        ("Cadair Idris via Minffordd Path", "hard", 10.0, 6.0, 893, 890, 52.6858, -3.9026),
        ("Y Garn Circuit", "moderate", 9.5, 5.5, 947, 730, 53.1167, -4.0167),
    ],
    "Lake District": [
        ("Scafell Pike via Corridor Route", "hard", 13.0, 7.0, 978, 900, 54.4486, -3.2306),
        ("Helvellyn via Striding Edge", "advanced", 12.5, 7.5, 950, 780, 54.5359, -2.9502),
        ("Catbells and Derwentwater", "moderate", 7.0, 3.5, 451, 360, 54.5860, -3.1720),
        ("Blencathra via Sharp Edge", "advanced", 9.0, 6.0, 868, 700, 54.6285, -3.0075),
        ("Old Man of Coniston", "moderate", 9.5, 4.5, 803, 620, 54.3697, -3.0782),
        ("Great Gable via Sty Head", "hard", 11.0, 6.5, 899, 810, 54.4880, -3.1690),
    ],
    "Scottish Highlands": [
        ("Ben Nevis via Mountain Track", "hard", 17.0, 8.0, 1345, 1350, 56.8175, -5.0713),
        ("Ben Nevis via CMD Arete", "advanced", 15.0, 9.5, 1345, 1400, 56.8200, -5.0100),
        ("Aonach Eagach Ridge", "advanced", 10.0, 8.0, 967, 1100, 56.6700, -5.0300),
        ("Buachaille Etive Mor", "hard", 11.0, 7.0, 1022, 900, 56.6402, -4.9022),
        ("Ben Lomond via Tourist Path", "moderate", 11.5, 5.5, 974, 950, 56.1642, -4.6350),
        ("Liathach Traverse", "advanced", 12.0, 9.0, 1055, 1150, 57.5500, -5.4500),
    ],
    "Peak District": [
        ("Kinder Scout via Jacob's Ladder", "moderate", 13.0, 5.5, 636, 480, 53.3733, -1.8127),
        ("Mam Tor Ridge Walk", "moderate", 9.0, 4.0, 517, 350, 53.3494, -1.8073),
        ("Bleaklow Circuit", "hard", 15.0, 6.5, 633, 470, 53.4478, -1.9319),
        ("Stanage Edge and Higger Tor", "moderate", 10.5, 4.5, 458, 300, 53.3467, -1.6297),
    ],
    "Brecon Beacons": [
        ("Pen y Fan via Corn Du", "moderate", 8.0, 3.5, 886, 500, 51.8797, -3.4356),
        ("Pen y Fan Horseshoe", "hard", 13.0, 6.0, 886, 750, 51.8890, -3.3990),
        ("Waun Fach", "moderate", 14.0, 6.0, 811, 600, 51.9200, -3.2200),
        ("Fan y Big Ridge", "hard", 12.0, 6.5, 719, 650, 51.8650, -3.4400),
    ],
    "Cairngorms": [
        ("Cairn Gorm via Ptarmigan", "moderate", 10.0, 5.0, 1245, 700, 57.1360, -3.6420),
        ("Ben Macdui via Coire Cas", "hard", 18.0, 9.0, 1309, 950, 57.1370, -3.6450),
        ("Cairngorm 4000s Traverse", "advanced", 26.0, 12.0, 1309, 1600, 56.9836, -3.5217),
        ("Lairig Ghru Crossing", "advanced", 31.0, 13.0, 835, 950, 57.1610, -3.7960),
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

# ---------------------------------------------------------------------------
# Extension layer — Review [Ext]
# ---------------------------------------------------------------------------
REVIEW_RESPONSE_RATE = 0.45

# Rating adjustment by route difficulty, added on top of the existing
# season adjustment. Reflects that harder routes are more physically
# demanding and weather-exposed, which on average nudges satisfaction down
# slightly even though they're popular and often the most memorable trips.
DIFFICULTY_RATING_ADJUSTMENT = {
    "moderate": 0.20,
    "hard": 0.0,
    "advanced": -0.35,
}

# Ops/weather cancellation probability by difficulty — harder routes run
# in more exposed terrain and are more weather-sensitive, so they're
# cancelled outright (guide/conditions call) somewhat more often.
DIFFICULTY_OPS_CANCEL_RATE = {
    "moderate": 0.04,
    "hard": 0.06,
    "advanced": 0.10,
}


# ---------------------------------------------------------------------------
# Extension layer — Weather [Ext]
# ---------------------------------------------------------------------------
# Rough climate profile per region: (summer_avg_c, winter_avg_c, storm_multiplier)
# Higher/more northerly regions are colder and stormier — Scottish
# Highlands and Cairngorms in particular.
REGION_CLIMATE = {
    "Snowdonia": (15.0, 4.0, 1.1),
    "Lake District": (15.5, 4.5, 1.0),
    "Scottish Highlands": (13.0, 1.0, 1.6),
    "Peak District": (16.0, 4.0, 0.8),
    "Brecon Beacons": (16.0, 4.5, 0.9),
    "Cairngorms": (12.0, -0.5, 1.7),
}

# ---------------------------------------------------------------------------
# Extension layer — Marketing / booking attribution [Ext]
# ---------------------------------------------------------------------------
# channel: (base_weight, cost_per_acquisition_gbp, conversion_rate, ctr)
# Organic/direct/referral are treated as ~zero-spend channels (typical for
# a small operator relying on SEO, word of mouth, and repeat visits) —
# ROAS is only meaningful for the paid channels.
MARKETING_CHANNELS = {
    "organic": (0.28, 0.0, 0.035, 0.0),
    "direct": (0.20, 0.0, 0.05, 0.0),
    "referral": (0.12, 0.0, 0.04, 0.0),
    "paid_search": (0.20, 24.0, 0.03, 0.045),
    "paid_social": (0.14, 17.0, 0.018, 0.012),
    "email": (0.06, 3.5, 0.08, 0.15),
}

CAMPAIGN_NAME_POOL = {
    "organic": ["SEO - Route Guides", "SEO - Blog Content"],
    "direct": ["Returning Customer Direct"],
    "referral": ["Partner Referral Programme", "Outdoor Forum Referrals"],
    "paid_search": ["Search - Snowdon Keywords", "Search - Munro Bagging", "Search - Brand"],
    "paid_social": ["Instagram - Winter Push", "Facebook - Summer Push", "Instagram - Retargeting"],
    "email": ["Monthly Newsletter", "Abandoned Booking Reminder"],
}

# ---------------------------------------------------------------------------
# Extension layer — WebsiteAnalytics [Ext]
# ---------------------------------------------------------------------------
DEVICES = {"mobile": 0.55, "desktop": 0.38, "tablet": 0.07}
BROWSERS = {"Chrome": 0.55, "Safari": 0.28, "Edge": 0.08, "Firefox": 0.06, "Other": 0.03}
VISITOR_COUNTRIES = {
    "United Kingdom": 0.84,
    "Ireland": 0.05,
    "Germany": 0.04,
    "United States": 0.04,
    "France": 0.03,
}

# ---------------------------------------------------------------------------
# Extension layer — EquipmentHire [Ext]
# ---------------------------------------------------------------------------
EQUIPMENT_HIRE_RATE = 0.40  # share of confirmed/amended bookings hiring anything
# item: (base_probability, price_gbp)
EQUIPMENT_ITEMS = {
    "boots": (0.45, 12.0),
    "waterproofs": (0.40, 15.0),
    "poles": (0.35, 8.0),
    "helmet": (0.20, 6.0),
    "ice_axe": (0.15, 10.0),
    "crampons": (0.15, 12.0),
}