"""Species-specific adjustment factor configuration."""

# Adjustment sensitivity for each species
# Values range from 0.0 (no effect) to 1.0 (maximum effect)
SPECIES_ADJUSTMENT_TRAITS = {
    # Original 6 species
    'ACPL': {  # Norway Maple
        'elevation_sensitivity': 0.7,  # Moderate response to elevation
        'urban_heat_island_effect': 0.6,  # Moderate UHI response
    },
    'ACRU': {  # Red Maple
        'elevation_sensitivity': 0.6,
        'urban_heat_island_effect': 0.7,
    },
    'LIST2': {  # Sweetgum
        'elevation_sensitivity': 0.5,  # Less sensitive to elevation
        'urban_heat_island_effect': 0.8,  # More sensitive to urban heat
    },
    'QURU': {  # Northern Red Oak
        'elevation_sensitivity': 0.8,  # Very sensitive to elevation
        'urban_heat_island_effect': 0.4,  # Less sensitive to UHI
    },
    'PSME': {  # Douglas Fir
        'elevation_sensitivity': 0.9,  # Evergreen, very elevation-sensitive
        'urban_heat_island_effect': 0.3,  # Less affected by urban conditions
    },
    'PRCE': {  # Cherry Plum
        'elevation_sensitivity': 0.6,
        'urban_heat_island_effect': 0.7,
    },

    # New 10 species
    'CRLA80': {  # Smooth Hawthorn
        'elevation_sensitivity': 0.6,
        'urban_heat_island_effect': 0.6,
    },
    'PYCA80': {  # Callery Pear
        'elevation_sensitivity': 0.5,
        'urban_heat_island_effect': 0.8,  # Thrives in urban areas
    },
    'BEPE3': {  # European White Birch
        'elevation_sensitivity': 0.8,  # Sensitive to elevation
        'urban_heat_island_effect': 0.5,
    },
    'ACPA2': {  # Japanese Maple
        'elevation_sensitivity': 0.7,
        'urban_heat_island_effect': 0.6,
    },
    'TICO2': {  # Littleleaf Linden
        'elevation_sensitivity': 0.5,
        'urban_heat_island_effect': 0.7,  # Common urban tree
    },
    'PRSE3': {  # Japanese Flowering Cherry
        'elevation_sensitivity': 0.6,
        'urban_heat_island_effect': 0.6,
    },
    'GLTR': {  # Honeylocust
        'elevation_sensitivity': 0.4,  # Adaptable
        'urban_heat_island_effect': 0.8,  # Urban tolerant
    },
    'CABE8': {  # European Hornbeam
        'elevation_sensitivity': 0.6,
        'urban_heat_island_effect': 0.7,
    },
    'COFL2': {  # Flowering Dogwood
        'elevation_sensitivity': 0.7,
        'urban_heat_island_effect': 0.5,  # Prefers natural settings
    },
    'FRLA': {  # Oregon Ash
        'elevation_sensitivity': 0.6,
        'urban_heat_island_effect': 0.5,  # Native, less urban-adapted
    },
}

# Default values for unknown species
DEFAULT_ADJUSTMENT_TRAITS = {
    'elevation_sensitivity': 0.6,
    'urban_heat_island_effect': 0.6,
}

def get_adjustment_traits(usda_symbol: str) -> dict:
    """Get adjustment sensitivity traits for a species."""
    return SPECIES_ADJUSTMENT_TRAITS.get(usda_symbol, DEFAULT_ADJUSTMENT_TRAITS)
