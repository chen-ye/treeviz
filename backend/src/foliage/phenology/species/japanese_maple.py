"""Japanese Maple (Acer palmatum) phenology model."""
from ..base import TreePhenologyModel

class JapaneseMaple(TreePhenologyModel):
    """
    Acer palmatum.
    Often red/purple foliage in summer (depending on cultivar).
    Vibrant red in fall.
    """
    def _resolve_daily_color(self, row) -> tuple[int, int, int]:
        # Phase 1: Palette
        structure_grey = (100, 100, 100)
        juvenile_red = (160, 60, 60)
        summer_red = (100, 40, 40) # Deep red/purple
        fall_crimson = (220, 20, 60)
        fall_orange = (255, 69, 0)
        bare_brown = (101, 67, 33)

        # --- Inputs ---
        gdd = row['accumulated_gdd']
        day_length = row['day_length']
        drought = row['drought_stress']
        is_freeze = row['recent_freeze']

        # --- Logic ---

        # 1. Spring (GDD)
        # Early leaf out: ~130 start, ~230 mature
        leaf_start = self.get_adjusted_threshold(130, 'gdd')
        leaf_mature = self.get_adjusted_threshold(230, 'gdd')

        if gdd < leaf_start:
            return structure_grey

        if gdd < leaf_mature:
            progress = self._calc_progress(gdd, leaf_start, leaf_mature)
            return self._interp_hsl(juvenile_red, summer_red, progress)

        # 2. Summer -> Fall
        # Medium fall timing.
        fall_start_dl = 11.5 + (drought * 1.0)
        fall_peak_dl = 10.5
        fall_end_dl = 9.5

        if day_length > fall_start_dl and not is_freeze:
            return summer_red

        # 3. Fall Progression
        if is_freeze:
            return bare_brown

        # Determine peak color based on sun/stress (simulated by UV stress)
        # High UV/Stress -> Brighter Red. Low -> Orange/Brown.
        target_peak = fall_crimson if row['uv_stress_factor'] > 0.1 else fall_orange

        if day_length > fall_peak_dl:
            # Summer Red -> Crimson/Orange
            progress = self._calc_progress(fall_start_dl - day_length, 0, fall_start_dl - fall_peak_dl)
            return self._interp_hsl(summer_red, target_peak, progress)
        elif day_length > fall_end_dl:
            # Crimson -> Brown
            progress = self._calc_progress(fall_peak_dl - day_length, 0, fall_peak_dl - fall_end_dl)
            return self._interp_hsl(target_peak, bare_brown, progress)
        else:
            return bare_brown
