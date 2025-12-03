"""Littleleaf Linden (Tilia cordata) phenology model."""
from ..base import TreePhenologyModel

class LittleleafLinden(TreePhenologyModel):
    """
    Tilia cordata. Heart-shaped leaves, yellow fall color.
    """
    def _resolve_daily_color(self, row) -> tuple[int, int, int]:
        dormant = (90, 80, 70)
        green = (34, 139, 34)
        yellow = (240, 230, 140) # Khaki/Yellow
        brown = (101, 67, 33)

        if row['accumulated_gdd'] < 160: return dormant

        if not row['is_fall_season']: return green

        # Fall
        if row['recent_freeze']: return brown

        chill = row['accumulated_chill']
        if chill < 150:
            return green
        elif 150 <= chill < 350:
            return self._interp(green, yellow, (chill-150)/200)
        else:
            return brown
