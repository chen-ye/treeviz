"""Douglas Fir (Pseudotsuga menziesii) phenology model."""
from ..base import TreePhenologyModel

class DouglasFir(TreePhenologyModel):
    """
    Pseudotsuga menziesii. Evergreen. Spring flush logic.
    """
    def _resolve_daily_color(self, row) -> tuple[int, int, int]:
        old_growth = (1, 68, 33)    # Dark Green
        new_growth = (100, 200, 50) # Lime Green tips

        # Spring Flush Logic (GDD)
        # Flush happens mid-spring
        if 250 <= row['accumulated_gdd'] < 450:
            # The "Flush" period where tips are bright
            # We interpolate back to dark as they harden off
            progress = (row['accumulated_gdd'] - 250) / 200
            # 0.0 = Peak Lime -> 1.0 = Hardened Dark
            return self._interp(new_growth, old_growth, progress)

        return old_growth
