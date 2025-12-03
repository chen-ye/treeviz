"""Japanese Flowering Cherry (Prunus serrulata) phenology model."""
from ..base import TreePhenologyModel

class JapaneseFloweringCherry(TreePhenologyModel):
    """
    Prunus serrulata. Famous spring bloom (pink/white), orange/bronze fall.
    """
    def _resolve_daily_color(self, row) -> tuple[int, int, int]:
        dormant = (100, 80, 80)
        green = (50, 100, 40)
        pink_bloom = (255, 183, 197)
        bronze_fall = (205, 127, 50)
        brown = (101, 67, 33)

        # Spring Bloom (Mid-Spring)
        if 150 <= row['accumulated_gdd'] < 300:
            return pink_bloom

        if row['accumulated_gdd'] < 150: return dormant

        if not row['is_fall_season']: return green

        # Fall
        if row['recent_freeze']: return brown

        chill = row['accumulated_chill']
        if chill < 100:
            return green
        elif 100 <= chill < 300:
            return self._interp(green, bronze_fall, (chill-100)/200)
        else:
            return brown
