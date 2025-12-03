"""Callery Pear (Pyrus calleryana) phenology model."""
from ..base import TreePhenologyModel

class CalleryPear(TreePhenologyModel):
    """
    Pyrus calleryana. Early white bloom, glossy green, late purple/red fall.
    """
    def _resolve_daily_color(self, row) -> tuple[int, int, int]:
        dormant = (90, 80, 80)
        glossy_green = (34, 139, 34)
        white_bloom = (255, 255, 255)
        purple_red = (128, 0, 32)
        brown = (101, 67, 33)

        # Early Bloom
        if 80 <= row['accumulated_gdd'] < 200:
            return white_bloom

        if row['accumulated_gdd'] < 80: return dormant

        if not row['is_fall_season']: return glossy_green

        # Late Fall Color
        if row['recent_freeze']: return brown

        chill = row['accumulated_chill']
        if chill < 250: # Holds green late
            return glossy_green
        elif 250 <= chill < 500:
            return self._interp(glossy_green, purple_red, (chill-250)/250)
        else:
            return brown
