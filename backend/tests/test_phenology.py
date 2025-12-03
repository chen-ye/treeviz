import pytest
from foliage.phenology import get_color_for_tree, interpolate_color, load_traits

def test_load_traits():
    traits = load_traits()
    assert "ACRU" in traits
    assert traits["ACRU"]["common_name"] == "Red Maple"

def test_interpolate_color():
    c1 = [0, 0, 0]
    c2 = [100, 100, 100]
    mid = interpolate_color(c1, c2, 0.5)
    assert mid == [50, 50, 50]

    start = interpolate_color(c1, c2, 0.0)
    assert start == c1

    end = interpolate_color(c1, c2, 1.0)
    assert end == c2

def test_get_color_for_tree_unknown_species():
    # Should return default green
    color = get_color_for_tree("UNKNOWN", 300)
    assert color == [34, 139, 34]

def test_get_color_for_tree_before_fall():
    # ACRU starts at 265
    color = get_color_for_tree("ACRU", 100)
    assert color == [34, 139, 34] # Green

def test_get_color_for_tree_peak():
    # ACRU peak at 290, color [220, 20, 60]
    color = get_color_for_tree("ACRU", 290)
    # The logic might not hit exactly peak color if float math varies, but should be close
    # At exactly peak DOY, progress = 1.0 in first branch or 0.0 in second branch.
    # Code:
    # if effective_doy < peak: ...
    # else: progress = (effective_doy - peak) / (end - peak); interpolate(target, brown, progress)
    # If effective_doy == peak, it goes to else block.
    # progress = 0.0. interpolate(target, brown, 0.0) -> target.
    assert color == [220, 20, 60]

def test_get_color_for_tree_after_fall():
    # ACRU ends at 315
    color = get_color_for_tree("ACRU", 350)
    assert color == [139, 69, 19] # Brown

def test_get_color_for_tree_transition():
    # ACRU start 265, peak 290.
    # Check midway: 277.5
    color = get_color_for_tree("ACRU", 277) # ~Halfway to peak
    # Should be blend of Green [34, 139, 34] and Red [220, 20, 60]
    # R: 34 -> 220 increasing
    # G: 139 -> 20 decreasing
    # B: 34 -> 60 increasing
    assert color[0] > 34
    assert color[1] < 139
    assert color[2] > 34

def test_weather_factor():
    # Weather factor > 1 shifts effective_doy forward (earlier in year essentially, or makes current day act like later day?)
    # Code: effective_doy = doy + (shift * 5); shift = (weather_factor - 1.0) * 10
    # If factor = 1.1 -> shift = 1.0 -> effective_doy = doy + 5.
    # So day 260 acts like 265.

    # ACRU start is 265.
    # Normal day 260: should be green (260 < 265).
    color_normal = get_color_for_tree("ACRU", 260, weather_factor=1.0)
    assert color_normal == [34, 139, 34]

    # Accelerated day 260 (acts like 265): should start changing?
    # At 265 exactly it starts changing?
    # Logic: if effective_doy < start: return base.
    # If effective_doy == start: interpolate(base, target, 0) -> base.
    # So 260 + 5 = 265. Still green but on the cusp.

    # Let's try 261 with weather factor. 261 + 5 = 266.
    # 266 > 265. Should be slightly red.
    color_accel = get_color_for_tree("ACRU", 261, weather_factor=1.1)

    # Normal 261 is green
    color_normal_261 = get_color_for_tree("ACRU", 261, weather_factor=1.0)
    assert color_normal_261 == [34, 139, 34]

    assert color_accel != color_normal_261
    assert color_accel[0] > 34 # Red component increased
