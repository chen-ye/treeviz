"""Honeylocust (Gleditsia triacanthos) phenology model."""
from ..base import TreePhenologyModel

class Honeylocust(TreePhenologyModel):
    """
    Gleditsia triacanthos. Late leaf out, clear yellow fall color.
    """
    def _resolve_daily_color(self, row) -> tuple[int, int, int]:
        dormant = (80, 70, 60)
        green = (85, 107, 47) # Olive green
        yellow = (255, 215, 0)
        brown = (101, 67, 33)

        # Late leaf out
        if row['accumulated_gdd'] < 220: return dormant

        if not row['is_fall_season']: return green

        # Fall - turns yellow early then drops quickly
        if row['recent_freeze']: return brown

        chill = row['accumulated_chill']
        if chill < 100:
            return green
        elif 100 <= chill < 250:
            return self._interp(green, yellow, (chill-100)/150)
        else:
            return brown # Drops early
