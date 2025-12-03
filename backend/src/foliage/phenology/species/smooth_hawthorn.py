"""Smooth Hawthorn (Crataegus laevigata) phenology model."""
from ..base import TreePhenologyModel

class SmoothHawthorn(TreePhenologyModel):
    """
    Crataegus laevigata. Late spring white flowers, red berries in fall.
    """
    def _resolve_daily_color(self, row) -> tuple[int, int, int]:
        dormant = (100, 90, 80)
        green = (60, 120, 50)
        white_bloom = (250, 250, 240)
        yellow_fall = (220, 180, 60)
        brown = (101, 67, 33)

        # Spring
        if row['accumulated_gdd'] < 150: return dormant

        # Bloom (Late Spring)
        if 250 <= row['accumulated_gdd'] < 350:
            return white_bloom

        if not row['is_fall_season']: return green

        # Fall
        if row['recent_freeze']: return brown

        chill = row['accumulated_chill']
        if chill < 150:
            return green
        elif 150 <= chill < 350:
            return self._interp(green, yellow_fall, (chill-150)/200)
        else:
            return brown
