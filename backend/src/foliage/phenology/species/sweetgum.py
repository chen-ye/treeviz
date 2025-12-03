"""Sweetgum (Liquidambar styraciflua) phenology model."""
from ..base import TreePhenologyModel

class Sweetgum(TreePhenologyModel):
    """
    Liquidambar styraciflua. Late fall color, highly variable vibrant mix (Red/Purple/Yellow).
    """
    def _resolve_daily_color(self, row) -> tuple[int, int, int]:
        summer_green = (34, 139, 34)
        vibrant_red = (220, 20, 60)
        deep_purple = (75, 0, 130)
        brown = (101, 67, 33)

        if row['accumulated_gdd'] < 250: return (100, 90, 80) # Late waker
        if not row['is_fall_season']: return summer_green
        if row['recent_freeze']: return brown

        chill = row['accumulated_chill']

        # Sweetgum needs MORE chill to start turning than maple
        if chill < 200:
            return summer_green
        elif 200 <= chill < 500:
            # Mix of red and purple based on UV/Sun
            target = vibrant_red if row['uv_stress_factor'] > 0.2 else deep_purple
            return self._interp(summer_green, target, (chill-200)/300)
        else:
            return brown
