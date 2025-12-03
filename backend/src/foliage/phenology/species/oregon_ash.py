"""Oregon Ash (Fraxinus latifolia) phenology model."""
from ..base import TreePhenologyModel

class OregonAsh(TreePhenologyModel):
    """
    Fraxinus latifolia. Native. Yellow fall color.
    """
    def _resolve_daily_color(self, row) -> tuple[int, int, int]:
        dormant = (110, 100, 90)
        green = (85, 107, 47)
        yellow = (255, 215, 0)
        brown = (101, 67, 33)

        # Late leaf out
        if row['accumulated_gdd'] < 200: return dormant

        if not row['is_fall_season']: return green

        # Fall
        if row['recent_freeze']: return brown

        chill = row['accumulated_chill']
        if chill < 100:
            return green
        elif 100 <= chill < 300:
            return self._interp(green, yellow, (chill-100)/200)
        else:
            return brown
