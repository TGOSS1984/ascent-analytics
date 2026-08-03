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
    "Yorkshire Dales",  # added to accommodate real routes.json data (Ingleborough) —
                        # not one of the original 6 synthetic regions, but a genuine
                        # addition rather than a restructure of what already existed
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
    #
    # Two sources feed this list:
    #  - The original 30 synthetic routes (seeded before real fixture data
    #    was available), coordinates approximate.
    #  - 27 real routes pulled directly from backend/fixtures/routes.json in
    #    the live UK Summit Guides app, coordinates exact (map_center_lat/lng
    #    from the fixture). The live app groups these into 5 regions
    #    (Scotland, Lake District, Wales, Peak District, Yorkshire Dales) —
    #    coarser than the 6 used here. Rather than restructure the existing
    #    6 regions, each real route is mapped to whichever of the 6 it's
    #    actually located in (e.g. a Wales-region route near Snowdon maps to
    #    "Snowdonia"). One real route (Ingleborough) doesn't fit any of the
    #    6 at all, so "Yorkshire Dales" was added as a 7th region — a
    #    genuine addition, not a restructure.
    #  - 4 near-duplicate routes (same real mountain/route, slightly
    #    different name/stats between the synthetic and real version — e.g.
    #    "Ben Nevis via CMD Arete" vs the real "Ben Nevis via CMD Arête")
    #    were upgraded to the real data in place, rather than kept as two
    #    near-identical entries.
    "Snowdonia": [
        ("Snowdon via Llanberis Path", "moderate", 14.5, 6.0, 1085, 975, 53.1201, -4.1174),
        ("Snowdon via Pyg Track", "hard", 12.0, 6.5, 1085, 920, 53.0912, -4.0567),
        ("Snowdon Horseshoe", "advanced", 11.0, 8.5, 1085, 1000, 53.0900, -4.0580),
        ("Tryfan North Ridge", "advanced", 6.5, 6.0, 918, 800, 53.1096, -4.0654),
        ("Cadair Idris via Minffordd Path", "hard", 10.0, 6.0, 893, 890, 52.6858, -3.9026),
        ("Y Garn Circuit", "moderate", 9.5, 5.5, 947, 730, 53.1167, -4.0167),
        # -- real routes from routes.json (region 3: Wales, Snowdonia sub-area) --
        ("Tryfan North Face & Bristly Ridge", "advanced", 9.0, 5.0, 1001, 1000, 53.1305, -3.9170),
        ("Snowdon via Crib Goch", "advanced", 12.0, 7.0, 1085, 1143, 53.0685, -4.0760),
        ("Cadair Idris", "hard", 10.0, 5.0, 893, 790, 52.6998, -3.9087),
        ("Cnicht", "moderate", 10.0, 4.0, 691, 500, 52.9976, -3.9741),
        ("Carnedd Dafydd via Crib Lem Spur", "hard", 15.0, 7.0, 1044, 1000, 53.1265, -3.9805),
        ("Moel Siabod", "hard", 9.0, 4.5, 872, 750, 53.1190, -3.8940),
        ("Nantlle Ridge", "hard", 9.0, 6.0, 734, 750, 53.0460, -4.1900),
        ("Pen yr Ole Wen", "hard", 5.8, 4.5, 978, 658, 53.1700, -3.9790),
    ],
    "Lake District": [
        ("Scafell Pike via Corridor Route", "hard", 13.0, 7.0, 978, 900, 54.4486, -3.2306),
        ("Helvellyn via Striding Edge", "advanced", 12.5, 7.5, 950, 780, 54.5359, -2.9502),
        ("Catbells and Derwentwater", "moderate", 7.0, 3.5, 451, 360, 54.5860, -3.1720),
        ("Blencathra via Sharp Edge", "hard", 13.2, 4.0, 868, 868, 54.6390, -3.0500),  # upgraded to real stats
        ("Old Man of Coniston", "moderate", 9.5, 4.5, 803, 620, 54.3697, -3.0782),
        ("Great Gable via Sty Head", "hard", 11.0, 6.5, 899, 810, 54.4880, -3.1690),
        # -- real routes from routes.json (region 2: Lake District) --
        ("Helvellyn via Striding Swirral Edge", "hard", 11.0, 5.0, 950, 800, 54.5270, -3.0165),
        ("Pavey Ark via Jack's Rake", "hard", 10.7, 4.0, 700, 700, 54.4480, -3.0720),
        ("Great Gable", "hard", 11.7, 5.0, 899, 899, 54.4825, -3.2206),
        ("Blencathra via Hall's Fell Ridge", "hard", 8.5, 4.0, 868, 750, 54.6390, -3.0500),
        ("Bowfell via Climbers' Traverse", "moderate", 12.9, 5.0, 902, 931, 54.4478, -3.1678),
        ("Scafell Pike via Lord's Rake", "hard", 13.0, 6.5, 978, 1356, 54.4543, -3.2110),
        ("Crinkle Crags", "moderate", 12.7, 4.0, 853, 750, 54.4470, -3.1500),
        ("Fairfield Horseshoe", "hard", 16.0, 7.0, 873, 1000, 54.4320, -2.9600),
        ("Pillar", "hard", 12.0, 5.0, 892, 800, 54.4970, -3.2630),
    ],
    "Scottish Highlands": [
        ("Ben Nevis via Mountain Track", "hard", 17.0, 8.0, 1345, 1350, 56.8175, -5.0713),
        ("Ben Nevis via CMD Arête", "advanced", 17.5, 8.0, 1345, 1506, 56.7969, -5.0035),  # upgraded to real stats
        ("Aonach Eagach Ridge", "advanced", 10.0, 8.0, 967, 1100, 56.6700, -5.0300),
        ("Buachaille Etive Mòr", "advanced", 13.0, 7.0, 1021, 1110, 56.6383, -4.9786),  # upgraded to real stats
        ("Ben Lomond via Tourist Path", "moderate", 11.5, 5.5, 974, 950, 56.1642, -4.6350),
        ("Liathach", "advanced", 11.5, 10.0, 1055, 1326, 57.5620, -5.5070),  # upgraded to real stats (was "Liathach Traverse")
        # -- real routes from routes.json (region 1: Scotland) --
        ("Ring of Steall", "advanced", 16.9, 10.0, 1099, 1600, 56.7720, -4.9390),
        ("Suilven", "advanced", 20.0, 8.5, 731, 1000, 58.1370, -5.1580),
        ("An Teallach", "advanced", 15.4, 8.0, 1062, 1270, 57.8070, -5.2520),
    ],
    "Peak District": [
        ("Kinder Scout via Jacob's Ladder", "moderate", 13.0, 5.5, 636, 480, 53.3733, -1.8127),
        ("Mam Tor Ridge Walk", "moderate", 9.0, 4.0, 517, 350, 53.3494, -1.8073),
        ("Bleaklow Circuit", "hard", 15.0, 6.5, 633, 470, 53.4478, -1.9319),
        ("Stanage Edge and Higger Tor", "moderate", 10.5, 4.5, 458, 300, 53.3467, -1.6297),
        # -- real route from routes.json (region 4: Peak District) --
        ("Kinder Scout via Red Brook", "moderate", 10.0, 4.0, 636, 500, 53.3840, -1.8750),
    ],
    "Brecon Beacons": [
        ("Pen y Fan via Corn Du", "moderate", 8.0, 3.5, 886, 500, 51.8797, -3.4356),
        ("Pen y Fan Horseshoe", "hard", 13.0, 6.0, 886, 750, 51.8890, -3.3990),
        ("Waun Fach", "moderate", 14.0, 6.0, 811, 600, 51.9200, -3.2200),
        ("Fan y Big Ridge", "hard", 12.0, 6.5, 719, 650, 51.8650, -3.4400),
        # -- real route from routes.json (region 3: Wales, Brecon Beacons sub-area) --
        ("Pen y fan", "moderate", 6.5, 4.0, 886, 600, 51.8830, -3.4360),
    ],
    "Cairngorms": [
        ("Cairn Gorm via Ptarmigan", "moderate", 10.0, 5.0, 1245, 700, 57.1360, -3.6420),
        ("Ben Macdui via Coire Cas", "hard", 18.0, 9.0, 1309, 950, 57.1370, -3.6450),
        ("Cairngorm 4000s Traverse", "advanced", 26.0, 12.0, 1309, 1600, 56.9836, -3.5217),
        ("Lairig Ghru Crossing", "advanced", 31.0, 13.0, 835, 950, 57.1610, -3.7960),
    ],
    "Yorkshire Dales": [
        # New region — added specifically because this real route from
        # routes.json doesn't fit any of the other 6.
        ("Ingleborough", "moderate", 17.0, 6.0, 723, 690, 54.1532, -2.3995),
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

# Guide discount tendency [Ext] — a business question: which guides offer
# bigger discounts, and does that show up as lower margin on their
# bookings? Most guides discount rarely or not at all; a handful have a
# noticeably higher tendency. Right-skewed on purpose (Beta(1.5, 8)
# scaled to a 0-25% range), not a uniform spread.
GUIDE_DISCOUNT_TENDENCY_ALPHA = 1.5
GUIDE_DISCOUNT_TENDENCY_BETA = 8.0
GUIDE_DISCOUNT_TENDENCY_MAX = 0.25

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
    "Yorkshire Dales": (15.5, 3.5, 0.9),  # similar upland-England profile to Peak District
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