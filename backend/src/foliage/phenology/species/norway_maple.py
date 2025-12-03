"""Norway Maple (Acer platanoides) phenology model."""
from ..base import TreePhenologyModel

class NorwayMaple(TreePhenologyModel):
    """
    Standard green to yellow/gold fall color.
    """
    def _resolve_daily_color(self, row) -> tuple[int, int, int]:
        green = (54, 124, 43)
        yellow = (255, 215, 0)
        brown = (101, 67, 33)

        if row['accumulated_gdd'] < 200:
            return (110, 100, 90) # Dormant/Buds

        if not row['is_fall_season']:
            return green

        if row['recent_freeze']: return brown
        if row['is_severe_drought']: return (160, 110, 60)

        chill = row['accumulated_chill']

        # UV/Elevation can add orange tints
        peak_color = yellow
        if row['uv_stress_factor'] > 0.3:
            peak_color = self._interp(yellow, (255, 140, 0), row['uv_stress_factor'])

        if chill < 100: return green
        elif 100 <= chill < 300:
            return self._interp(green, peak_color, (chill-100)/200)
        elif 300 <= chill < 450:
            return self._interp(peak_color, brown, (chill-300)/150)
        else:
            return brown
