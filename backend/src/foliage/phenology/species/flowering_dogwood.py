"""Flowering Dogwood (Cornus florida) phenology model."""
from ..base import TreePhenologyModel

class FloweringDogwood(TreePhenologyModel):
    """
    Cornus florida. Spring white/pink bracts, red fall color.
    """
    def _resolve_daily_color(self, row) -> tuple[int, int, int]:
        dormant = (100, 90, 90)
        green = (60, 100, 60)
        white_bloom = (255, 250, 240)
        red_fall = (178, 34, 34)
        brown = (101, 67, 33)

        # Spring Bloom (Early-Mid)
        if 120 <= row['accumulated_gdd'] < 250:
            return white_bloom

        if row['accumulated_gdd'] < 120: return dormant

        if not row['is_fall_season']: return green

        # Fall
        if row['recent_freeze']: return brown

        chill = row['accumulated_chill']
        if chill < 100:
            return green
        elif 100 <= chill < 300:
            return self._interp(green, red_fall, (chill-100)/200)
        else:
            return brown
