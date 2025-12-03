"""Test the adjustment factor calculation."""
from src.foliage.phenology.adjustments import calculate_adjustment_days, shift_color_timeline
from src.foliage.phenology.adjustment_traits import get_adjustment_traits

def test_adjustment_factors():
    print("Testing Adjustment Factor Calculations\n")
    print("=" * 60)

    # Test Case 1: Higher elevation tree
    print("\nTest 1: Higher Elevation Tree (Norway Maple)")
    print("-" * 60)
    adj_days = calculate_adjustment_days(
        species_symbol='ACPL',  # Norway Maple
        tree_elevation=200.0,    # Tree at 200m
        tree_is_urban=False,
        grid_elevation=100.0,    # Grid average 100m
        grid_is_urban=False
    )
    traits = get_adjustment_traits('ACPL')
    print(f"Tree Elevation: 200m, Grid Elevation: 100m")
    print(f"Elevation Sensitivity: {traits['elevation_sensitivity']}")
    print(f"→ Adjustment: {adj_days} days {'(earlier)' if adj_days < 0 else '(later)'}")

    # Test Case 2: Urban tree in non-urban grid
    print("\n\nTest 2: Urban Tree (Callery Pear)")
    print("-" * 60)
    adj_days = calculate_adjustment_days(
        species_symbol='PYCA80',  # Callery Pear (urban-tolerant)
        tree_elevation=50.0,
        tree_is_urban=True,       # Urban tree
        grid_elevation=50.0,
        grid_is_urban=False        # Non-urban grid average
    )
    traits = get_adjustment_traits('PYCA80')
    print(f"Tree: Urban=True, Grid: Urban=False")
    print(f"UHI Sensitivity: {traits['urban_heat_island_effect']}")
    print(f"→ Adjustment: {adj_days} days {'(earlier)' if adj_days < 0 else '(later)'}")

    # Test Case 3: Combined effect
    print("\n\nTest 3: Combined Effects (Douglas Fir)")
    print("-" * 60)
    adj_days = calculate_adjustment_days(
        species_symbol='PSME',    # Douglas Fir (high elevation sensitivity,  low UHI)
        tree_elevation=300.0,      # High elevation
        tree_is_urban=False,
        grid_elevation=100.0,
        grid_is_urban=True         # Grid is urban but tree isn't
    )
    traits = get_adjustment_traits('PSME')
    print(f"Elevation Delta: +200m, Urban Delta: Non-urban in urban grid")
    print(f"Elevation Sensitivity: {traits['elevation_sensitivity']}")
    print(f"UHI Sensitivity: {traits['urban_heat_island_effect']}")
    print(f"→ Combined Adjustment: {adj_days} days {'(earlier)' if adj_days < 0 else '(later)'}")

    # Test Case 4: Timeline shifting
    print("\n\nTest 4: Timeline Shifting")
    print("-" * 60)
    # Mock timeline (simplified for demo)
    mock_timeline = [
        (100, 100, 100),  # Day 0: Dormant
        (150, 200, 150),  # Day 1: Spring
        (0, 255, 0),       # Day 2: Peak green
        (255, 255, 0),     # Day 3: Fall yellow
        (139, 69, 19)      # Day 4: Fall brown
    ]

    shifted_timeline = shift_color_timeline(mock_timeline, -1)  # Advance by 1 day
    print("Original Day 1:", mock_timeline[1])
    print("Shifted Day 1:", shifted_timeline[1])
    print("(Day 1 now shows what was Day 2)")

    print("\n" + "=" * 60)
    print("✓ All tests completed successfully!")

if __name__ == "__main__":
    test_adjustment_factors()
