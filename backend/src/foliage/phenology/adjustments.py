"""Adjustment factor calculation for per-tree phenology variations."""
from .adjustment_traits import get_adjustment_traits

def calculate_adjustment_days(
    species_symbol: str,
    tree_elevation: float,
    tree_is_urban: bool,
    grid_elevation: float,
    grid_is_urban: bool
) -> int:
    """
    Calculate timeline adjustment in days based on tree-specific vs grid-average conditions.

    Args:
        species_symbol: USDA symbol for the species
        tree_elevation: Tree's elevation in meters
        tree_is_urban: Tree's urban status
        grid_elevation: Grid cell's average elevation
        grid_is_urban: Grid cell's urban status

    Returns:
        Days to shift timeline (negative = earlier, positive = later)
    """
    traits = get_adjustment_traits(species_symbol)
    total_adjustment = 0.0

    # 1. Elevation Adjustment
    # Rule: Higher elevation → earlier phenology (especially fall color)
    # Effect: ~5-7 days per 100m elevation difference at full sensitivity
    if tree_elevation is not None and grid_elevation is not None:
        elevation_delta = tree_elevation - grid_elevation
        elevation_sensitivity = traits['elevation_sensitivity']

        # Base: 6 days per 100m
        elevation_adjustment = -(elevation_delta / 100.0) * 6.0 * elevation_sensitivity
        total_adjustment += elevation_adjustment

    # 2. Urban Heat Island Adjustment
    # Rule: Urban areas → delayed fall, extended growing season
    # Effect: ~3-5 days delay at full sensitivity
    urban_delta = 0
    if tree_is_urban is not None and grid_is_urban is not None:
        if tree_is_urban and not grid_is_urban:
            # Tree is urban but grid average is not → delay
            urban_delta = 1
        elif not tree_is_urban and grid_is_urban:
            # Tree is not urban but grid average is → advance
            urban_delta = -1

    if urban_delta != 0:
        urban_sensitivity = traits['urban_heat_island_effect']
        # Base: 4 days
        urban_adjustment = urban_delta * 4.0 * urban_sensitivity
        total_adjustment += urban_adjustment

    # Round to nearest day
    return round(total_adjustment)

def shift_color_timeline(timeline: list[tuple[int, int, int]], days: int) -> list[tuple[int, int, int]]:
    """
    Shift a color timeline by a number of days.

    Args:
        timeline: List of 365/366 (R, G, B) tuples
        days: Number of days to shift (negative = earlier, positive = later)

    Returns:
        Shifted timeline (same length as input)
    """
    if days == 0 or not timeline:
        return timeline

    length = len(timeline)
    shifted = []

    for i in range(length):
        # Map current day to source day
        source_index = (i - days) % length
        shifted.append(timeline[source_index])

    return shifted
