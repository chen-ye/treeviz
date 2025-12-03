"""Douglas Fir (Pseudotsuga menziesii) phenology model."""
from ..base import TreePhenologyModel

class DouglasFir(TreePhenologyModel):
    """
    Pseudotsuga menziesii.
    Evergreen.
    Spring flush (lime green tips).
    """
    def _resolve_daily_color(self, row) -> tuple[int, int, int]:
        # Phase 1: Palette
        deep_green = (1, 68, 33)
        lime_flush = (130, 200, 80)
        winter_green = (1, 55, 30) # Slightly darker/duller in winter

        # --- Inputs ---
        gdd = row['accumulated_gdd']
        is_freeze = row['recent_freeze']
        is_fall = row['is_fall_season']

        # --- Logic ---

        # 1. Spring Flush (GDD)
        # Flush starts ~250, Peaks ~350, Hardens off by ~600
        flush_start = self.get_adjusted_threshold(250, 'gdd')
        flush_peak = self.get_adjusted_threshold(350, 'gdd')
        harden_end = self.get_adjusted_threshold(600, 'gdd')

        if gdd < flush_start:
            # Winter/Early Spring
            # If very cold, maybe slightly brownish/duller?
            return winter_green if is_freeze else deep_green

        if gdd < harden_end:
            # Flushing
            if gdd < flush_peak:
                # Dark -> Lime
                progress = self._calc_progress(gdd, flush_start, flush_peak)
                return self._interp_hsl(deep_green, lime_flush, progress)
            else:
                # Lime -> Dark
                progress = self._calc_progress(gdd, flush_peak, harden_end)
                return self._interp_hsl(lime_flush, deep_green, progress)

        # 2. Summer/Fall/Winter
        return deep_green
