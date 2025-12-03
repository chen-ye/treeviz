"""Japanese Maple (Acer palmatum) phenology model."""
from ..base import TreePhenologyModel

class JapaneseMaple(TreePhenologyModel):
    """
    Acer palmatum. Often red/purple foliage in summer, vibrant red in fall.
    """
    def _resolve_daily_color(self, row) -> tuple[int, int, int]:
        dormant = (100, 80, 80)
        summer_red = (100, 40, 40) # Many cultivars are reddish
        vibrant_red = (220, 20, 60)
        orange = (255, 69, 0)
        brown = (101, 67, 33)

        if row['accumulated_gdd'] < 130: return dormant

        if not row['is_fall_season']: return summer_red

        # Fall
        if row['recent_freeze']: return brown

        chill = row['accumulated_chill']
        if chill < 100:
            return summer_red
        elif 100 <= chill < 300:
            # Transition to vibrant red/orange
            target = vibrant_red if row['uv_stress_factor'] > 0.2 else orange
            return self._interp(summer_red, target, (chill-100)/200)
        else:
            return brown
