"""Cherry Plum (Prunus cerasifera) phenology model."""
from ..base import TreePhenologyModel

class CherryPlum(TreePhenologyModel):
    """
    Early spring flowering, dark purple foliage variant (Prunus cerasifera 'Nigra').
    """
    def _resolve_daily_color(self, row) -> tuple[int, int, int]:
        # Colors
        dormant = (100, 80, 80)      # Dark Brown/Grey
        bloom = (255, 192, 203)      # Pink
        foliage = (80, 20, 40)       # Deep Purple
        faded_fall = (100, 60, 40)   # Dull Bronze

        # Spring Logic (GDD)
        # Blooms early: ~150 GDD
        if row['accumulated_gdd'] < 100:
            return dormant
        elif 100 <= row['accumulated_gdd'] < 250:
            # Flowering Phase
            return bloom
        elif not row['is_fall_season']:
            # Summer Foliage
            return foliage

        # Fall Logic
        if row['recent_freeze']: return (60, 40, 30) # Dead

        chill = row['accumulated_chill']
        if chill < 100:
            return foliage
        else:
            # Fades to bronze then drops
            return self._interp(foliage, faded_fall, (chill - 100)/200)
