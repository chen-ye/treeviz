"""European White Birch (Betula pendula) phenology model."""
from ..base import TreePhenologyModel

class EuropeanWhiteBirch(TreePhenologyModel):
    """
    Betula pendula. Early yellow fall color, drops leaves early.
    """
    def _resolve_daily_color(self, row) -> tuple[int, int, int]:
        dormant = (180, 180, 170) # White bark visible
        light_green = (144, 238, 144)
        bright_yellow = (255, 255, 0)
        brown = (139, 69, 19)

        if row['accumulated_gdd'] < 120: return dormant

        if not row['is_fall_season']: return light_green

        # Early Fall
        if row['recent_freeze']: return brown
        if row['is_drought']: return bright_yellow # Stress yellows early

        chill = row['accumulated_chill']
        if chill < 50:
            return light_green
        elif 50 <= chill < 200:
            return self._interp(light_green, bright_yellow, (chill-50)/150)
        else:
            return brown # Drops early
