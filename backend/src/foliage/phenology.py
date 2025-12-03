import json
import logging
import math
from datetime import datetime, timedelta

# Simple in-memory cache for demo
traits_cache = {}

def load_traits():
    if not traits_cache:
        try:
            # Try loading relative to package
            import os
            base_dir = os.path.dirname(__file__)
            path = os.path.join(base_dir, "phenology_traits.json")
            with open(path, "r") as f:
                traits_cache.update(json.load(f))
        except Exception as e:
            logging.error(f"Failed to load phenology traits: {e}")
    return traits_cache

def get_color_for_tree(usda_symbol: str, doy: int, weather_factor: float = 1.0):
    """
    Returns a calculated RGB color for a tree on a given Day of Year.
    weather_factor: Multiplier for speed of transition (1.0 = normal, >1.0 = faster/earlier due to cold/drought).
    """
    traits = load_traits()
    trait = traits.get(usda_symbol)

    # Default Green
    base_color = [34, 139, 34]

    if not trait:
        return base_color

    start = trait["fall_start_doy"]
    peak = trait["fall_peak_doy"]
    end = trait["fall_end_doy"]
    target_color = trait["peak_color"]

    # Adjust for weather (heuristic: Cold/Drought shifts start earlier)
    # If weather_factor > 1 (e.g. 1.1), start shifts earlier by ~10% of window?
    # Let's say weather_factor shifts the whole window.
    shift = (weather_factor - 1.0) * 10 # 1.1 -> 1 day earlier? Maybe 1.1 -> 10% faster accumulation?
    # Simple shift:
    effective_doy = doy + (shift * 5) # Artificial acceleration

    if effective_doy < start:
        return base_color
    elif effective_doy > end:
        # Brown/Bare
        return [139, 69, 19]

    # Interpolate
    if effective_doy < peak:
        # Green -> Peak
        progress = (effective_doy - start) / (peak - start)
        return interpolate_color(base_color, target_color, progress)
    else:
        # Peak -> Brown
        progress = (effective_doy - peak) / (end - peak)
        return interpolate_color(target_color, [139, 69, 19], progress)

def interpolate_color(c1, c2, t):
    return [
        int(c1[0] + (c2[0] - c1[0]) * t),
        int(c1[1] + (c2[1] - c1[1]) * t),
        int(c1[2] + (c2[2] - c1[2]) * t)
    ]
