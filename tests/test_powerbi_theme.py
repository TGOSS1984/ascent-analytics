"""Validates the Power BI report theme JSON is well-formed and has the
fields Power BI Desktop expects."""

import json
import re

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
    hex_pattern = re.compile(r"^#[0-9A-Fa-f]{6}$")
    with open(THEME_PATH) as f:
        theme = json.load(f)

    for color in theme["dataColors"]:
        assert hex_pattern.match(color), f"{color} is not a valid hex color"
    for key in ["background", "foreground", "tableAccent", "good", "neutral", "bad", "maximum", "center", "minimum", "null"]:
        assert hex_pattern.match(theme[key]), f"{key}={theme[key]} is not a valid hex color"


def test_visualstyles_colors_use_nested_solid_object_not_plain_string():
    """Power BI's theme schema requires color properties inside
    visualStyles to be {"solid": {"color": "#hex"}} objects — a plain hex
    string validates fine in the top-level fields (dataColors, background,
    etc.) but fails silently different, confusing schema errors when used
    inside visualStyles. This walks the whole visualStyles tree and flags
    any *Color/*colour key whose value is a bare string.
    """
    with open(THEME_PATH) as f:
        theme = json.load(f)

    color_key_pattern = re.compile(r"(color|Color)$")
    offenders = []

    def walk(node, path, parent_key=None):
        if isinstance(node, dict):
            for key, value in node.items():
                new_path = f"{path}/{key}"
                is_color_key = bool(color_key_pattern.search(key))
                # A bare hex string is only legitimate as the innermost
                # leaf of a {"solid": {"color": "#hex"}} wrapper — i.e.
                # when this key is "color" and its immediate parent key is
                # "solid". Anywhere else, a *Color/*color key must hold a
                # {"solid": {...}} object, not a plain string.
                is_legitimate_leaf = key == "color" and parent_key == "solid"
                if is_color_key and isinstance(value, str) and not is_legitimate_leaf:
                    offenders.append(new_path)
                else:
                    walk(value, new_path, parent_key=key)
        elif isinstance(node, list):
            for i, item in enumerate(node):
                walk(item, f"{path}[{i}]", parent_key=parent_key)

    walk(theme.get("visualStyles", {}), "visualStyles", parent_key=None)
    assert not offenders, f"Plain-string colors found where an object is required: {offenders}"