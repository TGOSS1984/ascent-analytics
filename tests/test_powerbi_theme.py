"""Validates the Power BI report theme JSON is well-formed and has the
fields Power BI Desktop expects."""

import json

from src.generation import config

THEME_PATH = config.PROJECT_ROOT / "powerbi" / "ascent_analytics_theme.json"


def test_theme_file_exists():
    assert THEME_PATH.exists()


def test_theme_is_valid_json():
    with open(THEME_PATH) as f:
        json.load(f)  # raises if malformed


def test_theme_has_required_top_level_fields():
    with open(THEME_PATH) as f:
        theme = json.load(f)
    required = {"name", "dataColors", "background", "foreground", "good", "neutral", "bad"}
    assert required.issubset(theme.keys())


def test_theme_has_at_least_eight_data_colors():
    with open(THEME_PATH) as f:
        theme = json.load(f)
    assert len(theme["dataColors"]) >= 8


def test_all_colors_are_valid_hex():
    import re

    hex_pattern = re.compile(r"^#[0-9A-Fa-f]{6}$")
    with open(THEME_PATH) as f:
        theme = json.load(f)

    for color in theme["dataColors"]:
        assert hex_pattern.match(color), f"{color} is not a valid hex color"
    for key in ["background", "foreground", "tableAccent", "good", "neutral", "bad", "maximum", "center", "minimum", "null"]:
        assert hex_pattern.match(theme[key]), f"{key}={theme[key]} is not a valid hex color"