"""European Hornbeam (Carpinus betulus) phenology model."""
from ..base import TreePhenologyModel

class EuropeanHornbeam(TreePhenologyModel):
    """
    Carpinus betulus. Dense green foliage, yellow/brown fall, marcescent (holds leaves).
    """
    def _resolve_daily_color(self, row) -> tuple[int, int, int]:
        dormant = (90, 80, 70)
        green = (34, 139, 34)
        yellow_brown = (184, 134, 11)
        dry_brown = (139, 69, 19)

        if row['accumulated_gdd'] < 150: return dormant

        if not row['is_fall_season']: return green

        # Fall
        chill = row['accumulated_chill']
        if chill < 200:
            return green
        elif 200 <= chill < 450:
            return self._interp(green, yellow_brown, (chill-200)/250)
        else:
            # Marcescent - holds dry brown leaves
            return dry_brown
