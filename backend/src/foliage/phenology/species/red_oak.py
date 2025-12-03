"""Northern Red Oak (Quercus rubra) phenology model."""
from ..base import TreePhenologyModel

class NorthernRedOak(TreePhenologyModel):
    """
    Quercus rubra. Late russet color. Marcescent (holds brown leaves).
    """
    def _resolve_daily_color(self, row) -> tuple[int, int, int]:
        green = (50, 100, 40)
        russet = (165, 42, 42) # Reddish Brown
        dry_brown = (139, 69, 19)

        if row['accumulated_gdd'] < 300: return (90, 80, 70) # Very late spring
        if not row['is_fall_season']: return green

        chill = row['accumulated_chill']

        # Oaks turn very late
        if chill < 300:
            return green
        elif 300 <= chill < 600:
            return self._interp(green, russet, (chill-300)/300)
        else:
            # Marcescence: They hold the brown leaves all winter
            return dry_brown
